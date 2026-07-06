"""Intelligence boundary: AI Brain, Agents, Guidance, Self-Improvement.

Rule: modules here PROPOSE actions; they never execute domain mutations
directly. Execution goes through intelligence.action_broker, which is
the only sanctioned bridge to the runtime/domain layer.
"""
from . import ai_brain, agent_layer, guidance_system, self_improvement  # noqa: F401
