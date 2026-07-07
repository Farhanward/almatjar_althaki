from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_'-]{1,}|[\u0600-\u06ff]{2,}", re.I)


def default_catalog() -> list[dict[str, Any]]:
    return [
        {"sku": "AUTO-START", "name": "AI Automation Starter", "price": 1499, "tags": ["automation", "workflow", "n8n"]},
        {"sku": "CHAT-WA", "name": "WhatsApp Sales Bot", "price": 2499, "tags": ["whatsapp", "sales", "support"]},
        {"sku": "SEO-GEO", "name": "GEO Visibility Pack", "price": 1999, "tags": ["seo", "geo", "content"]},
        {"sku": "SEC-GUARD", "name": "AI Security Guard", "price": 2999, "tags": ["security", "audit", "proxy"]},
    ]


def save_catalog(path: str | Path, catalog: list[dict[str, Any]] | None = None) -> dict:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = catalog or default_catalog()
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"out": str(out.resolve()), "products": len(rows)}


def load_catalog(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        save_catalog(p)
    return json.loads(p.read_text(encoding="utf-8"))


def recommend(message: str, catalog: list[dict[str, Any]]) -> dict:
    tokens = {m.group(0).casefold() for m in TOKEN_RE.finditer(message)}
    scored = []
    for product in catalog:
        score = len(tokens.intersection({str(tag).casefold() for tag in product.get("tags", [])}))
        if str(product.get("sku", "")).casefold() in tokens:
            score += 3
        scored.append((score, product))
    score, product = max(scored, key=lambda item: (item[0], -float(item[1].get("price", 0))))
    return {"product": product, "score": score, "reason": "مطابقة كلمات العميل مع tags المنتج."}


def handle_store_message(message: str, catalog: list[dict[str, Any]]) -> dict:
    low = message.casefold()
    rec = recommend(message, catalog)
    action = "ANSWER"
    # الاسترجاع/الإلغاء أولاً: «ألغِ طلبي» تحتوي كلمة «طلب» لكنها حالة دعم لا شراء.
    if any(word in low for word in ("refund", "cancel", "استرجاع", "الغاء", "إلغاء")):
        action = "ESCALATE_SUPPORT"
    elif any(word in low for word in ("buy", "order", "اشتري", "طلب")):
        action = "CREATE_DRAFT_ORDER"
    return {"action": action, "recommendation": rec, "reply": f"أقترح {rec['product']['name']} بسعر {rec['product']['price']} ريال."}

