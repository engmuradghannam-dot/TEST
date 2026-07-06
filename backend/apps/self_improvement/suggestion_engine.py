"""Suggestion Engine: persists analyzer output; humans approve/reject."""
import logging

from .analyzer import AIAnalyzer
from .models import ImprovementSuggestion

logger = logging.getLogger(__name__)

MIN_CONFIDENCE = 0.5


class SuggestionEngine:
    def generate(self) -> int:
        created = 0
        for s in AIAnalyzer().analyze():
            if s.get("confidence", 0) < MIN_CONFIDENCE:
                continue
            if ImprovementSuggestion.objects.filter(
                    title=s["title"], status__in=["proposed", "approved"]).exists():
                continue
            ImprovementSuggestion.objects.create(
                area=s["area"], title=s["title"], analysis=s["analysis"],
                proposed_change=s.get("proposed_change", {}),
                confidence=s.get("confidence", 0),
            )
            created += 1
        logger.info("suggestion engine created %s suggestions", created)
        return created
