# المتجر الذكي AlMatjar AlThaki

المتجر الذكي الجاهز نواة متجر محلي: كتالوج منتجات، توصية حسب رسالة العميل، إنشاء طلب مسودة، وتصعيد دعم. لا ينفذ دفعاً حقيقياً.

## آلية العمل

1. `init-catalog` ينشئ كتالوج خدمات/منتجات.
2. `handle` يحلل رسالة عميل ويقترح منتجاً وaction.
3. `convert-bitext` يحول رسائل Bitext إلى أحداث متجر.
4. `batch/stress` يقيسان عدم الانهيار وعدد الطلبات/التصعيدات.

## تشغيل سريع

```powershell
python -m almatjar_althaki.cli init-catalog
python -m almatjar_althaki.cli handle --message "I want to buy WhatsApp bot"
python -m almatjar_althaki.cli convert-bitext
python -m almatjar_althaki.cli batch
```

## بيانات الاختبار

تعتمد على بيانات Bitext التي جلبها `C:\Projects\almandoub` من الإنترنت بعدد 12,000 رسالة.

## آخر نتائج

- الاختبارات الذاتية: 2/2 ناجحة.
- الكتالوج الافتراضي: 4 منتجات/خدمات.
- Benchmark: 12,000 معالجة، errors=0، draft_orders=1,989، escalations=969، p99=0.098ms.
- Stress: 36,000 معالجة، errors=0، draft_orders=5,967، escalations=2,907، p99=0.091ms، peak memory=1.19MB.

## تحسينات إنتاجية 2026-07-04

- المتجر لا ينفذ دفعاً ولا طلباً حقيقياً؛ ينشئ `CREATE_DRAFT_ORDER` فقط، وهذا آمن للاختبار.
- التوصية مبنية على tags/SKU وتعيد سبباً واضحاً، حتى يسهل لاحقاً استبدالها بمحرك أقوى.
- batch/stress يقيسان الطلبات المسودة والتصعيدات بجانب الأخطاء.

## التشغيل المؤسسي (Enterprise) — v1.0.0

- **خدمة متجر عبر HTTP**: `python -m almatjar_althaki.cli serve` → `POST /api/handle {"message"}` يعيد `ANSWER/CREATE_DRAFT_ORDER/ESCALATE_SUPPORT` مع توصيات.
- **draft-only**: لا دفع ولا طلب حقيقي — آمن للربط المباشر بقنوات العملاء.
- **الكتالوج يحمل مرة واحدة** عند الإقلاع (`ALMATJAR_CATALOG`، افتراضي `data\catalog.json`).
- **نقاط فحص**: `/api/health` (مفتوح) · `/api/version` · `/api/metrics`.
- **تهيئة عبر البيئة**: متغيرات `ALMATJAR_*` — انظر `docs/OPERATIONS.md`.
- **مصادقة**: `ALMATJAR_API_KEY` → ترويسة `X-API-Key`. **سجلات JSON**: `logs\almatjar-althaki.service.jsonl`.

## التشغيل المؤسسي (Enterprise) — v1.0.0

- **خدمة متجر عبر HTTP**: `python -m almatjar_althaki.cli serve` → `POST /api/handle {"message"}` يعيد `ANSWER/CREATE_DRAFT_ORDER/ESCALATE_SUPPORT` مع توصيات.
- **draft-only**: لا دفع ولا طلب حقيقي — آمن للربط المباشر بقنوات العملاء.
- **إصلاح v1.0.0**: الاسترجاع/الإلغاء له الأولوية على نية الشراء («ألغِ طلبي» تصعّد للدعم ولا تنشئ طلباً).
- **الكتالوج يحمل مرة واحدة** عند الإقلاع (`ALMATJAR_CATALOG`، افتراضي `data\catalog.json`).
- **نقاط فحص**: `/api/health` (مفتوح) · `/api/version` · `/api/metrics`.
- **تهيئة عبر البيئة**: متغيرات `ALMATJAR_*` — انظر `docs/OPERATIONS.md`.
- **مصادقة**: `ALMATJAR_API_KEY` → ترويسة `X-API-Key`. **سجلات JSON**: `logs\almatjar-althaki.service.jsonl`.
