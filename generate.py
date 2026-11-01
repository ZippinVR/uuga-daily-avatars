import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

# AEST is UTC+10 year-round.
aest = timezone(timedelta(hours=10))
today = datetime.now(aest).date().isoformat()

entries = json.loads(Path("avatars.json").read_text(encoding="utf-8"))
pool = [entry["id"] for entry in entries]

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
