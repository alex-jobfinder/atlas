from __future__ import annotations

import gzip
import json
import math
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class DataPointSeries(BaseModel):
    """Discrete time series with uniform step.

    - start_ms: epoch millis for the first sample
    - step_ms: spacing between adjacent samples in milliseconds
    - values: numeric samples (float("nan") allowed)
    - name: optional label
    """

    start_ms: int
    step_ms: int
    values: list[float]
    name: str | None = None

    @property
    def end_ms(self) -> int:
        if not self.values:
            return self.start_ms
        return self.start_ms + self.step_ms * (len(self.values) - 1)


class GraphDefPy(BaseModel):
    """Minimal graph definition mirroring Scala GraphDef structure for Python usage.

    Consists of one or more DataPointSeries to be rendered as lines/spans downstream.
    """

    start_ms: int
    end_ms: int
    step_ms: int
    series: list[DataPointSeries] = Field(default_factory=list)

    @classmethod
    def from_single_series(cls, series: DataPointSeries) -> GraphDefPy:
        return cls(start_ms=series.start_ms, end_ms=series.end_ms, step_ms=series.step_ms, series=[series])


class EngineDataGenerator:
    """Replicates key data-generation helpers from Scala PngGraphEngineSuite in Python.

    Provides:
      - constant series
      - sine wave series (wave)
      - interval switching between two series over a time window
      - helpers for simple/fine-grained waves
      - loaders for V1 (API-style) JSON and V2 (JsonCodec) JSON(.gz)
    """

    def __init__(self, default_step_ms: int = 60_000) -> None:
        self.default_step_ms = default_step_ms

    # ---------- Synthetic Series Generators ----------

    def constant(
        self,
        value: float,
        *,
        start_ms: int | None = None,
        step_ms: int | None = None,
        num_points: int = 1,
        name: str | None = None,
    ) -> DataPointSeries:
        start = start_ms if start_ms is not None else self._epoch_ms(2012, 1, 1)
        step = step_ms if step_ms is not None else self.default_step_ms
        return DataPointSeries(
            start_ms=start, step_ms=step, values=[float(value)] * num_points, name=name or str(value)
        )

    def wave(
        self,
        min_value: float,
        max_value: float,
        wavelength_ms: int,
        *,
        start_ms: int | None = None,
        step_ms: int | None = None,
        num_points: int = 1440,
        name: str | None = None,
    ) -> DataPointSeries:
        start = start_ms if start_ms is not None else self._epoch_ms(2012, 1, 1)
        step = step_ms if step_ms is not None else self.default_step_ms
        amplitude = (max_value - min_value) / 2.0
        yoffset = min_value + amplitude
        angular = 2.0 * math.pi / float(wavelength_ms)

        values: list[float] = []
        for i in range(num_points):
            t_ms = start + i * step
            v = amplitude * math.sin(t_ms * angular) + yoffset
            values.append(v)
        return DataPointSeries(start_ms=start, step_ms=step, values=values, name=name or "wave")

    def interval(
        self,
        base: DataPointSeries,
        override: DataPointSeries,
        interval_start_ms: int,
        interval_end_ms: int,
        *,
        name: str | None = None,
    ) -> DataPointSeries:
        """Select values from 'override' within [interval_start_ms, interval_end_ms), else 'base'.

        Both input series must share start_ms and step_ms and have equal length.
        """
        self._ensure_compatible_series(base, override)
        if len(base.values) != len(override.values):
            raise ValueError("Base and override series must have the same number of samples")

        values: list[float] = []
        for i, v in enumerate(base.values):
            t_ms = base.start_ms + i * base.step_ms
            if interval_start_ms <= t_ms < interval_end_ms:
                values.append(override.values[i])
            else:
                values.append(v)

        return DataPointSeries(start_ms=base.start_ms, step_ms=base.step_ms, values=values, name=name or base.name)

    def finegrain_wave(
        self,
        min_value: int,
        max_value: int,
        hours: int,
        *,
        start_ms: int | None = None,
        step_ms: int | None = None,
        name: str | None = None,
    ) -> DataPointSeries:
        wavelength_ms = hours * 60 * 60 * 1000
        num_points = max(1, int((24 * 60 * 60 * 1000) / (step_ms or self.default_step_ms)))
        return self.wave(
            min_value, max_value, wavelength_ms, start_ms=start_ms, step_ms=step_ms, num_points=num_points, name=name
        )

    def simple_wave(
        self,
        min_value: float,
        max_value: float,
        *,
        start_ms: int | None = None,
        step_ms: int | None = None,
        name: str | None = None,
    ) -> DataPointSeries:
        """Daily sine wave similar to Scala simpleWave(min, max)."""
        return self.wave(
            min_value,
            max_value,
            wavelength_ms=24 * 60 * 60 * 1000,
            start_ms=start_ms,
            step_ms=step_ms,
            num_points=1440,
            name=name,
        )

    # ---------- JSON Loaders ----------

    def load_v1_graph_json(self, path: str | Path, *, name: str | None = None) -> GraphDefPy:
        """Load V1 API-style graph JSON (used in atlas tests) into GraphDefPy.

        Expects fields: start (ms), step (ms), values: List[List[float]].
        """
        p = Path(path)
        data = json.loads(p.read_text())
        start_ms = int(data["start"])  # epoch millis
        step_ms = int(data["step"])  # millis
        # Flatten inner singleton lists: values: [[v0],[v1],...] -> [v0,v1,...]
        flat: list[float] = [
            float(row[0]) if isinstance(row, list) and row else float(row) for row in data.get("values", [])
        ]
        series = DataPointSeries(
            start_ms=start_ms, step_ms=step_ms, values=flat, name=name or (data.get("legend") or [None])[0]
        )
        return GraphDefPy.from_single_series(series)

    def read_v2_json(self, path: str | Path) -> dict:
        """Read V2 JsonCodec JSON (optionally .gz). Returns raw dict for downstream mapping.

        This does not attempt to fully interpret atlas JsonCodec; caller can translate as needed.
        """
        p = Path(path)
        raw: bytes
        if p.suffix == ".gz":
            with gzip.open(p, "rb") as f:
                raw = f.read()
        else:
            raw = p.read_bytes()
        return json.loads(raw.decode("utf-8"))

    # ---------- Examples to mirror Scala tests ----------

    def example_non_uniformly_drawn_spikes(self, v1_json_path: str | Path) -> GraphDefPy:
        """Mirror test("non_uniformly_drawn_spikes"): load V1 JSON and set width semantics upstream.

        Width is handled by renderer; here we return the data/time configuration.
        """
        return self.load_v1_graph_json(v1_json_path)

    def example_one_data_point_wide_spike(self) -> GraphDefPy:
        """Construct a sequence with sparse spikes similar to the Scala test case."""
        # Time bounds
        start = self._to_epoch_ms(datetime(2013, 6, 9, 18, 0, 0, tzinfo=UTC))
        end = self._to_epoch_ms(datetime(2013, 6, 11, 18, 0, 0, tzinfo=UTC))
        step = 3 * 60_000  # 3 minutes
        # number of inclusive samples between start and end at 3m step
        num_points = 1 + int((end - start) / step)
        values = [0.0] * num_points
        for idx in (0, 10, 690, num_points - 1):
            if 0 <= idx < num_points:
                values[idx] = 0.005553
        series = DataPointSeries(start_ms=start, step_ms=step, values=values, name="one_point_spike")
        return GraphDefPy.from_single_series(series)

    # ---------- Internal helpers ----------

    def _ensure_compatible_series(self, a: DataPointSeries, b: DataPointSeries) -> None:
        if a.start_ms != b.start_ms or a.step_ms != b.step_ms:
            raise ValueError("Series must have the same start_ms and step_ms to combine")

    @staticmethod
    def _epoch_ms(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> int:
        return EngineDataGenerator._to_epoch_ms(datetime(year, month, day, hour, minute, second, tzinfo=UTC))

    @staticmethod
    def _to_epoch_ms(dt: datetime) -> int:
        return int(dt.timestamp() * 1000)


__all__ = [
    "DataPointSeries",
    "EngineDataGenerator",
    "GraphDefPy",
]
