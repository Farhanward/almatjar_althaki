from __future__ import annotations

import json
from pathlib import Path


def convert_bitext(input_path: str | Path, out_path: str | Path, *, limit: int = 0) -> dict:
    source = Path(input_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with source.open("r", encoding="utf-8") as handle, out.open("w", encoding="utf-8") as output:
        for line in handle:
            if limit and rows >= limit:
                break
            if not line.strip():
                continue
            rec = json.loads(line)
            output.write(json.dumps({"message": rec.get("instruction") or "", "intent": rec.get("intent"), "category": rec.get("category")}, ensure_ascii=False) + "\n")
            rows += 1
    return {"source": str(source.resolve()), "out": str(out.resolve()), "rows": rows}

