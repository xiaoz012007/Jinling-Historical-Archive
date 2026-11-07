"""Reproduce this Task004 sample from the exact frozen CSV; standard library only."""
import csv, hashlib, json, random, sys
from pathlib import Path
p = Path(sys.argv[1])
expected = '769050746ba52cbaf61acbb675bbcd09ca00d0c8df9e7764df4954deba545764'
actual = hashlib.sha256(p.read_bytes()).hexdigest()
if actual != expected:
    raise SystemExit('Input SHA-256 differs; do not reuse the frozen sample for another version.')
with p.open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
if len(rows) != 157:
    raise SystemExit('Expected 157 data records.')
indices = random.Random(19371213).sample(range(157), 10)
print(json.dumps({'input_sha256':actual, 'python_version':sys.version, 'seed':19371213,
                  'indices':indices, 'event_ids':[rows[i]['event_id'] for i in indices]},
                 ensure_ascii=False, indent=2))
