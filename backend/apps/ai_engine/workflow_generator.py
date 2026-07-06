"""AI Workflow Generator.

Turns a natural-language description into a workflow definition
(states + transitions + guards) compatible with apps.workflow models,
validated before persistence.
"""
import json
import logging

from .llm_providers import MultiProviderLLM
from .context_engine import ContextEngine

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an ERP workflow designer. Respond ONLY with JSON:
{
  "name": str,
  "description": str,
  "states": [{"name": str, "is_initial": bool, "is_final": bool}],
  "transitions": [{"from": str, "to": str, "action": str,
                   "guards": [{"type": "permission|role|condition|amount",
                               "config": {}}]}]
}
No markdown fences, no commentary."""


class AIWorkflowGenerator:
    def __init__(self):
        self.llm = MultiProviderLLM()
        self.context = ContextEngine()

    def generate(self, company, description: str) -> dict:
        prompt = self.context.build(company, f"Design workflow: {description}",
                                    include_erp_state=False)
        resp = self.llm.complete(prompt, system=SYSTEM_PROMPT, max_tokens=2000)
        raw = resp.text.strip().removeprefix("```json").removesuffix("```").strip()
        spec = json.loads(raw)
        self._validate(spec)
        return spec

    def _validate(self, spec: dict):
        states = {s["name"] for s in spec.get("states", [])}
        if not states:
            raise ValueError("Workflow has no states")
        initials = [s for s in spec["states"] if s.get("is_initial")]
        if len(initials) != 1:
            raise ValueError("Workflow must have exactly one initial state")
        for t in spec.get("transitions", []):
            if t["from"] not in states or t["to"] not in states:
                raise ValueError(f"Transition references unknown state: {t}")

    def persist(self, company, spec: dict):
        from apps.workflow.models import Workflow, WorkflowState, WorkflowTransition
        wf = Workflow.objects.create(
            company=company, name=spec["name"],
            description=spec.get("description", ""),
        )
        state_objs = {}
        for s in spec["states"]:
            state_objs[s["name"]] = WorkflowState.objects.create(
                workflow=wf, name=s["name"],
                is_initial=s.get("is_initial", False),
                is_final=s.get("is_final", False),
            )
        for t in spec["transitions"]:
            WorkflowTransition.objects.create(
                workflow=wf, from_state=state_objs[t["from"]],
                to_state=state_objs[t["to"]], action=t.get("action", ""),
                guards=t.get("guards", []),
            )
        return wf
