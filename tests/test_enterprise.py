"""Enterprise-layer tests: config, metrics, hardened HTTP store service."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from almatjar_althaki.config import load_config
from almatjar_althaki.observability import Metrics, teardown_logging
from almatjar_althaki.service import Handler, create_server
from almatjar_althaki.version import __version__


class ConfigTests(unittest.TestCase):
    KEYS = ("ALMATJAR_HOME", "ALMATJAR_API_KEY", "ALMATJAR_PORT")

    def setUp(self) -> None:
        self._saved = {k: os.environ.get(k) for k in self.KEYS}

    def tearDown(self) -> None:
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_defaults(self) -> None:
        for key in self.KEYS:
            os.environ.pop(key, None)
        cfg = load_config()
        self.assertEqual(cfg.port, 8802)
        self.assertFalse(cfg.auth_required)

    def test_env_overrides(self) -> None:
        os.environ["ALMATJAR_API_KEY"] = "k"
        os.environ["ALMATJAR_PORT"] = "9919"
        cfg = load_config()
        self.assertTrue(cfg.auth_required)
        self.assertEqual(cfg.port, 9919)


class MetricsTests(unittest.TestCase):
    def test_percentiles_ordered(self) -> None:
        metrics = Metrics("almatjar-althaki", __version__)
        for value in range(1, 41):
            metrics.observe_ms(float(value))
        snap = metrics.snapshot()
        self.assertLessEqual(snap["latency_ms"]["p50"], snap["latency_ms"]["p95"])
        self.assertLessEqual(snap["latency_ms"]["p95"], snap["latency_ms"]["p99"])


class ServiceTestBase(unittest.TestCase):
    api_key = ""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ["ALMATJAR_API_KEY"] = self.api_key
        os.environ["ALMATJAR_LOG_DIR"] = str(Path(self._tmp.name) / "logs")
        self.server = create_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        for key in ("ALMATJAR_API_KEY", "ALMATJAR_LOG_DIR"):
            os.environ.pop(key, None)
        if Handler.logger is not None:
            teardown_logging(Handler.logger)
            Handler.logger = None
        self._tmp.cleanup()

    def request(self, path: str, payload: dict | None = None, headers: dict | None = None):
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=data, headers=headers or {})
        if data is not None:
            request.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))


class OpenServiceTests(ServiceTestBase):
    api_key = ""

    def test_health(self) -> None:
        status, body = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["service"], "almatjar-althaki")

    def test_handle_purchase_intent(self) -> None:
        status, body = self.request("/api/handle", {"message": "I want to buy and place an order now"})
        self.assertEqual(status, 200)
        self.assertIn(body["action"], {"ANSWER", "CREATE_DRAFT_ORDER", "ESCALATE_SUPPORT"})

    def test_handle_refund_escalates(self) -> None:
        status, body = self.request("/api/handle", {"message": "I want a refund, please cancel my order"})
        self.assertEqual(status, 200)
        self.assertEqual(body["action"], "ESCALATE_SUPPORT")

    def test_handle_missing_message(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.request("/api/handle", {})
        self.assertEqual(ctx.exception.code, 400)

    def test_metrics_after_handle(self) -> None:
        self.request("/api/handle", {"message": "what do you sell"})
        status, metrics = self.request("/api/metrics")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(metrics["counters"].get("http_requests_total", 0), 1)


class AuthServiceTests(ServiceTestBase):
    api_key = "matjar-secret"

    def test_rejects_missing_key(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.request("/api/metrics")
        self.assertEqual(ctx.exception.code, 401)

    def test_accepts_valid_key(self) -> None:
        status, body = self.request("/api/metrics", headers={"X-API-Key": "matjar-secret"})
        self.assertEqual(status, 200)
        self.assertEqual(body["service"], "almatjar-althaki")

    def test_health_open_for_probes(self) -> None:
        status, body = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["auth_required"])

    def test_oversized_body_rejected(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.request("/api/handle", {"message": "x" * 1_200_000}, headers={"X-API-Key": "matjar-secret"})
        self.assertEqual(ctx.exception.code, 413)


if __name__ == "__main__":
    unittest.main()
