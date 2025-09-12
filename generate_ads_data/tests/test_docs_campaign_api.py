from __future__ import annotations

from pathlib import Path

import pytest


def test_campaign_api_callback_docs(tmp_path: Path) -> None:
    """Build docs and verify the campaign API callback page renders details.

    Specifically, ensure the cb_create_advertiser docstring content appears in
    the generated HTML, demonstrating Option A wiring works.
    """
    pytest.importorskip("sphinx")
    from sphinx.cmd.build import main as sphinx_build_main  # type: ignore

    repo_root = Path(__file__).resolve().parents[1]
    docs_src = repo_root / "docs"
    outdir = tmp_path / "html"

    rc = sphinx_build_main(["-b", "html", "-q", str(docs_src), str(outdir)])
    assert rc == 0, "Sphinx build failed"

    api_html = (outdir / "api" / "campaign_api.html").read_text(encoding="utf-8")
    # Spot-check a key phrase from the Google-style docstring
    assert (
        "Advertiser name when not using" in api_html
    ), "Expected detailed Args text from cb_create_advertiser to appear in docs"
