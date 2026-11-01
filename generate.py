import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID
import csv
import io
from urllib.request import urlopen

# AEST is UTC+10 year-round.
aest = timezone(timedelta(hours=10))
today = datetime.now(aest).date().isoformat()

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRKCBvohgSUP2XK1hfpbI5SENB39gAOyC3jSnBq9OEVOrG34ruPkx8S9DZcgjdZn0X66vb8eKPNVXoZ/pub?output=csv"

with urlopen(SHEET_CSV_URL, timeout=30) as response:
    csv_text = response.read().decode("utf-8-sig")

reader = csv.DictReader(io.StringIO(csv_text))

if not reader.fieldnames or "id" not in reader.fieldnames:
    raise ValueError(
        "The Google Sheet must have an 'id' column. "
        "Check that the URL is the published CSV link."
    )

pool = []

for row_number, row in enumerate(reader, start=2):
    avatar_id = (row.get("id") or "").strip()
    name = (row.get("name") or "").strip()

    # Ignore completely empty rows.
    if not avatar_id and not name:
        continue

    if not avatar_id:
        raise ValueError(
            f"Sheet row {row_number}: '{name}' is missing its avatar ID."
        )

    pool.append(avatar_id)

if not isinstance(pool, list) or len(pool) < 3:
    raise ValueError("avatars.json must contain at least three avatar IDs.")

for avatar_id in pool:
    if not isinstance(avatar_id, str) or not avatar_id.startswith("avtr_"):
        raise ValueError(f"Invalid avatar ID: {avatar_id}")
    UUID(avatar_id[5:])

if len(pool) != len(set(pool)):
    raise ValueError("The avatar pool contains duplicate IDs.")

# A reproducible daily shuffle:
# rerunning on the same AEST date gives the same selection.
selected = sorted(
    pool,
    key=lambda avatar_id: hashlib.sha256(
        f"{today}:{avatar_id}".encode("utf-8")
    ).digest(),
)[:3]

payload = {
    "date": today,
    "timezone": "Australia/Brisbane",
    "avatarIds": selected,
}

output = Path("_site")
output.mkdir(exist_ok=True)

(output / "daily.json").write_text(
    json.dumps(payload, indent=2) + "\n",
    encoding="utf-8",
)

(output / "index.html").write_text(
    '<!doctype html><html><head><title>Daily Avatars</title></head>'
    '<body><a href="daily.json">View daily avatar selection</a></body></html>',
    encoding="utf-8",
)

print(json.dumps(payload, indent=2))
