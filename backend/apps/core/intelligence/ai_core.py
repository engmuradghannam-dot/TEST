"""Nexus AI Core — the unifying facade over the intelligence layer.

        Nexus AI Engine
              |
   ┌──────────┼───────────┬──────────────┬───────────────┐
 Agents   ML/Predictive  Knowledge     Decision       Automation
 (agent_   (predictive    Graph         Engine         Engine
  layer)    .py)          (knowledge_   (decision_     (guidance_
                          graph)        engine)        system)

This module wires the pieces into one object (`ai_core`) so callers have
a single entry point, and documents the architecture the components form.
"""
import logging

logger = logging.getLogger('nexus.ai_core')


class NexusAICore:
    @property
    def agents(self):
        from apps.core.intelligence.agent_layer import AgentOrchestrator
        return AgentOrchestrator()

    @property
    def predictive(self):
        from apps.core.intelligence import predictive
        return predictive

    @property
    def knowledge_graph(self):
        from apps.core.intelligence.knowledge_graph import graph
        return graph

    @property
    def decisions(self):
        from apps.core.intelligence.decision_engine import engine
        return engine

    @property
    def nl(self):
        from apps.core.intelligence.nlp_erp import nl_erp
        return nl_erp

    def health(self) -> dict:
        status = {}
        for name in ['agents', 'predictive', 'knowledge_graph',
                     'decisions', 'nl']:
            try:
                getattr(self, name)
                status[name] = 'available'
            except Exception as exc:  # noqa: BLE001
                status[name] = f'unavailable: {exc}'
        return status


ai_core = NexusAICore()
