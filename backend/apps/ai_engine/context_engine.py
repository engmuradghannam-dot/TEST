"""Context Engine: assembles company-scoped business context for AI calls.

Pulls live ERP data (inventory alerts, pending approvals, recent activity)
plus RAG memory hits into a single structured context block.
"""
from .rag_memory import RAGMemory


class ContextEngine:
    def __init__(self):
        self.rag = RAGMemory()

    def build(self, company, query: str, include_erp_state: bool = True) -> str:
        sections = [f"## Company\n{company.name} (id={company.pk})"]

        memory_hits = self.rag.query(company.pk, query, n_results=5)
        if memory_hits:
            joined = "\n".join(f"- {h['text'][:300]}" for h in memory_hits)
            sections.append(f"## Relevant memory\n{joined}")

        if include_erp_state:
            sections.append(self._erp_snapshot(company))

        sections.append(f"## User query\n{query}")
        return "\n\n".join(sections)

    def _erp_snapshot(self, company) -> str:
        lines = []
        try:
            from apps.inventory.models import Item
            low = Item.objects.filter(company=company).extra(
                where=["quantity_on_hand <= reorder_level"]
            )[:10] if hasattr(Item, "reorder_level") else []
            if low:
                lines.append("Low stock items: " + ", ".join(i.name for i in low))
        except Exception:
            pass
        try:
            from apps.workflow.models import ApprovalRecord
            pending = ApprovalRecord.objects.filter(
                company=company, status="pending"
            ).count()
            lines.append(f"Pending approvals: {pending}")
        except Exception:
            pass
        return "## ERP state\n" + ("\n".join(lines) if lines else "(no live signals)")
