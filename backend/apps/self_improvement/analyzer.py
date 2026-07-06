"""AI Analyzer: reads recent metrics/alerts, asks the LLM for diagnostics."""
import json
from datetime import timedelta

from django.utils import timezone


class AIAnalyzer:
    def collect_signals(self, hours: int = 24) -> dict:
        from apps.observability.models import Metric, Alert
        since = timezone.now() - timedelta(hours=hours)
        metrics = list(Metric.objects.filter(recorded_at__gte=since)
                       .values("name", "value", "recorded_at")[:500])
        alerts = list(Alert.objects.filter(fired_at__gte=since)
                      .values("category", "severity", "title", "status"))
        return {"metrics": metrics, "alerts": alerts}

    def analyze(self) -> list[dict]:
        from apps.ai_engine.llm_providers import MultiProviderLLM
        signals = self.collect_signals()
        prompt = (
            "Analyze these ERP system signals and propose improvements.\n"
            f"Signals: {json.dumps(signals, default=str)[:8000]}\n"
            'Respond ONLY with JSON list: [{"area": "performance|reliability|'
            'workflow|config", "title": str, "analysis": str, '
            '"proposed_change": {}, "confidence": 0.0-1.0}]'
        )
        resp = MultiProviderLLM().complete(prompt, max_tokens=2000)
        raw = resp.text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(raw)
