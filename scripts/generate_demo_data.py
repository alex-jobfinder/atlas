import json
from pathlib import Path
from datetime import datetime, timedelta
import random
import pandas as pd


def generate_data(path: Path = Path('tests/data/minute_ad_events.parquet')) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.utcnow().replace(second=0, microsecond=0)
    rows = []
    countries = ['US', 'CA', 'MX']
    for i in range(10):
        ts = now - timedelta(minutes=i)
        for country in countries:
            rows.append({
                'timestamp': ts.isoformat(),
                'impressions': random.randint(100, 1000),
                'country': country,
            })
    df = pd.DataFrame(rows)
    df.to_parquet(path, index=False)


def generate_manifest(path: Path = Path('manifest.json')) -> None:
    manifest = {
        'metrics': {
            'minute_ad_events.impressions': {
                'name': 'impressions',
                'dimensions': ['country'],
                'aggregation': 'sum',
            }
        }
    }
    path.write_text(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    generate_data()
    generate_manifest()
    print('Generated minute_ad_events.parquet and manifest.json')
