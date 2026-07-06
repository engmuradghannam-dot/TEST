"""
Guidance System for Nexus CE-ERP OS
AI Assistant that guides users, answers questions, suggests actions, auto-navigates
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from django.db import models
from django.utils import timezone
import uuid

from apps.core.intelligence.ai_brain import llm_core, rag_memory, context_engine, AIConversation, AIPromptTemplate
from apps.core.intelligence.agent_layer import AgentOrchestrator, AgentTask, AgentAction, agent_orchestrator
from apps.core.runtime.event_bus import event_bus, DomainEvent, EventTypes, EventPriority

logger = logging.getLogger(__name__)


class GuidanceSystem:
    """Main AI Assistant that provides guidance within the ERP"""

    SYSTEM_PROMPT = """You are the Nexus AI Assistant - an intelligent ERP guide.

Your capabilities:
1. Answer questions about ERP functionality
2. Guide users through complex processes
3. Suggest next actions based on context
4. Explain business logic and workflows
5. Help with troubleshooting
6. Provide training and tutorials
7. Navigate users to relevant pages

Guidelines:
- Respond in the user's preferred language (Arabic/English)
- Be concise but thorough
- Always suggest actionable next steps
- Reference specific ERP modules and features
- Provide step-by-step instructions when needed
- Use the user's role and permissions context
- If unsure, ask clarifying questions

Current date: {current_date}
User role: {user_role}
Company: {company_name}
"""

    def __init__(self):
        self.llm = llm_core
        self.rag = rag_memory
        self.context = context_engine
        self.orchestrator = agent_orchestrator

    def process_message(self, message: str, user, conversation_id: str = None,
                       current_page: str = None, context_data: Dict = None) -> Dict:
        """Process user message and generate response"""

        # Build context
        user_ctx = self.context.build_user_context(user)
        company_ctx = None
        if user.company:
            company_ctx = self.context.build_company_context(user.company)

        system_prompt = self.SYSTEM_PROMPT.format(
            current_date=datetime.now().strftime('%Y-%m-%d'),
            user_role=user_ctx.role,
            company_name=company_ctx.name if company_ctx else 'Unknown'
        )

        # Get or create conversation
        conversation = self._get_conversation(conversation_id, user)

        # Add user message
        conversation.add_message('user', message, {
            'current_page': current_page,
            'context_data': context_data
        })

        # Determine intent
        intent = self._classify_intent(message)

        # Route to appropriate handler
        if intent == 'how_to':
            response = self._handle_how_to(message, user_ctx, company_ctx, conversation)
        elif intent == 'why_delayed':
            response = self._handle_status_inquiry(message, user_ctx, company_ctx, conversation)
        elif intent == 'next_step':
            response = self._handle_next_step(message, user_ctx, company_ctx, conversation, context_data)
        elif intent == 'create':
            response = self._handle_creation_request(message, user_ctx, company_ctx, conversation)
        elif intent == 'analyze':
            response = self._handle_analysis_request(message, user_ctx, company_ctx, conversation)
        elif intent == 'navigate':
            response = self._handle_navigation(message, user_ctx, company_ctx)
        else:
            response = self._handle_general(message, user_ctx, company_ctx, conversation)

        # Add assistant response to conversation
        conversation.add_message('assistant', response['text'], {
            'intent': intent,
            'actions': response.get('suggested_actions', []),
            'navigation': response.get('navigation', {})
        })

        response['conversation_id'] = str(conversation.id)
        return response

    def _get_conversation(self, conversation_id: str, user) -> AIConversation:
        """Get or create conversation"""
        if conversation_id:
            try:
                return AIConversation.objects.get(id=conversation_id, user=user)
            except AIConversation.DoesNotExist:
                pass

        return AIConversation.objects.create(
            user=user,
            title="New Conversation",
            messages=[]
        )

    def _classify_intent(self, message: str) -> str:
        """Classify user intent from message"""
        message_lower = message.lower()

        how_to_keywords = ['how', 'كيف', 'طريقة', 'شرح', 'steps', 'guide']
        status_keywords = ['why', 'status', 'delayed', 'late', 'تأخر', 'متأخر', 'حالة']
        next_step_keywords = ['next', 'after', 'then', 'what now', 'الخطوة التالية', 'بعد']
        create_keywords = ['create', 'new', 'add', 'إنشاء', 'جديد', 'إضافة']
        analyze_keywords = ['analyze', 'report', 'summary', 'تحليل', 'تقرير', 'ملخص']
        navigate_keywords = ['go to', 'open', 'navigate', 'page', 'اذهب', 'افتح', 'صفحة']

        for keyword in how_to_keywords:
            if keyword in message_lower:
                return 'how_to'
        for keyword in status_keywords:
            if keyword in message_lower:
                return 'why_delayed'
        for keyword in next_step_keywords:
            if keyword in message_lower:
                return 'next_step'
        for keyword in create_keywords:
            if keyword in message_lower:
                return 'create'
        for keyword in analyze_keywords:
            if keyword in message_lower:
                return 'analyze'
        for keyword in navigate_keywords:
            if keyword in message_lower:
                return 'navigate'

        return 'general'

    def _handle_how_to(self, message: str, user_ctx, company_ctx, conversation) -> Dict:
        """Handle "how to" questions"""
        # Get relevant knowledge
        knowledge = self.rag.query(
            "company_knowledge",
            message,
            tenant_id=user_ctx.company_id
        )

        context_messages = conversation.get_context_messages()

        prompt = f"""User asks: {message}

Provide step-by-step instructions for completing this task in the ERP system.
Include:
1. Prerequisites
2. Step-by-step process
3. Required permissions
4. Common pitfalls
5. Related features

Context: {json.dumps([k['text'] for k in knowledge[:3]])}
"""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT.format(
                current_date=datetime.now().strftime('%Y-%m-%d'),
                user_role=user_ctx.role,
                company_name=company_ctx.name if company_ctx else 'Unknown'
            ),
            context=context_messages
        )

        return {
            'text': response['text'],
            'intent': 'how_to',
            'suggested_actions': [
                {'type': 'navigate', 'label': 'Go to relevant module', 'target': self._extract_module(message)},
                {'type': 'create', 'label': 'Create new', 'target': self._extract_document_type(message)}
            ],
            'navigation': self._extract_navigation(message)
        }

    def _handle_status_inquiry(self, message: str, user_ctx, company_ctx, conversation) -> Dict:
        """Handle status/delay inquiries"""
        # Extract document reference
        doc_info = self._extract_document_reference(message)

        prompt = f"""User is asking about status/delay of: {message}

Document info: {json.dumps(doc_info)}

Provide:
1. Possible reasons for delay
2. How to check current status
3. Who to contact
4. How to expedite
5. Prevention for future
"""

        response = self.llm.generate(prompt=prompt)

        return {
            'text': response['text'],
            'intent': 'status_inquiry',
            'suggested_actions': [
                {'type': 'view', 'label': 'View document', 'target': doc_info},
                {'type': 'escalate', 'label': 'Escalate', 'target': doc_info}
            ],
            'navigation': {'page': doc_info.get('module', ''), 'params': doc_info}
        }

    def _handle_next_step(self, message: str, user_ctx, company_ctx, conversation, context_data) -> Dict:
        """Handle "what's next" questions"""
        current_state = context_data.get('current_state', '') if context_data else ''
        document_type = context_data.get('document_type', '') if context_data else ''

        prompt = f"""User wants to know next steps.
Current state: {current_state}
Document type: {document_type}

Provide:
1. Immediate next actions
2. Alternative paths
3. Required approvals
4. Timeline expectations
5. Related tasks to complete
"""

        response = self.llm.generate(prompt=prompt)

        return {
            'text': response['text'],
            'intent': 'next_step',
            'suggested_actions': self._extract_actions_from_text(response['text']),
            'navigation': self._extract_navigation_from_actions(response['text'])
        }

    def _handle_creation_request(self, message: str, user_ctx, company_ctx, conversation) -> Dict:
        """Handle creation requests"""
        doc_type = self._extract_document_type(message)

        prompt = f"""User wants to create: {message}

Document type: {doc_type}

Provide:
1. Required fields
2. Prerequisites
3. Approval workflow
4. Related documents to link
5. Best practices
"""

        response = self.llm.generate(prompt=prompt)

        return {
            'text': response['text'],
            'intent': 'creation',
            'suggested_actions': [
                {'type': 'create_form', 'label': f'Create {doc_type}', 'target': doc_type},
                {'type': 'template', 'label': 'Use template', 'target': doc_type}
            ],
            'navigation': {'page': f'{doc_type.lower()}-create', 'params': {}}
        }

    def _handle_analysis_request(self, message: str, user_ctx, company_ctx, conversation) -> Dict:
        """Handle analysis/report requests"""
        # Dispatch to appropriate agent
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_type=self._determine_agent_type(message),
            action=AgentAction.ANALYZE,
            target_module=self._extract_module(message),
            target_id=None,
            parameters={
                'company_id': user_ctx.company_id,
                'query': message,
                'user_context': user_ctx.to_dict()
            }
        )

        agent_result = self.orchestrator.dispatch(task)

        return {
            'text': agent_result.get('analysis', agent_result.get('error', 'Analysis completed')),
            'intent': 'analysis',
            'suggested_actions': [
                {'type': 'report', 'label': 'View detailed report', 'target': task.target_module},
                {'type': 'export', 'label': 'Export data', 'target': task.target_module}
            ],
            'agent_result': agent_result
        }

    def _handle_navigation(self, message: str, user_ctx, company_ctx) -> Dict:
        """Handle navigation requests"""
        target = self._extract_navigation_target(message)

        return {
            'text': f"Navigating to {target.get('label', 'requested page')}...",
            'intent': 'navigation',
            'navigation': target,
            'suggested_actions': []
        }

    def _handle_general(self, message: str, user_ctx, company_ctx, conversation) -> Dict:
        """Handle general questions"""
        context_messages = conversation.get_context_messages()

        response = self.llm.generate(
            prompt=message,
            system_prompt=self.SYSTEM_PROMPT.format(
                current_date=datetime.now().strftime('%Y-%m-%d'),
                user_role=user_ctx.role,
                company_name=company_ctx.name if company_ctx else 'Unknown'
            ),
            context=context_messages
        )

        return {
            'text': response['text'],
            'intent': 'general',
            'suggested_actions': self._extract_actions_from_text(response['text'])
        }

    # Helper methods
    def _extract_module(self, message: str) -> str:
        modules = ['accounts', 'inventory', 'buying', 'selling', 'hr', 'crm', 'projects', 'manufacturing']
        for m in modules:
            if m in message.lower():
                return m
        return ''

    def _extract_document_type(self, message: str) -> str:
        docs = ['invoice', 'purchase order', 'sales order', 'employee', 'project', 'task']
        for d in docs:
            if d in message.lower():
                return d.replace(' ', '_')
        return ''

    def _extract_document_reference(self, message: str) -> Dict:
        import re
        # Extract PO/SO/Invoice numbers
        patterns = [
            (r'PO[-]?\d+', 'purchase_order'),
            (r'SO[-]?\d+', 'sales_order'),
            (r'INV[-]?\d+', 'invoice'),
        ]
        for pattern, doc_type in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return {'type': doc_type, 'number': match.group()}
        return {}

    def _extract_navigation(self, message: str) -> Dict:
        module = self._extract_module(message)
        if module:
            return {'page': module, 'params': {}}
        return {}

    def _extract_navigation_target(self, message: str) -> Dict:
        targets = {
            'dashboard': {'page': '/', 'label': 'Dashboard'},
            'purchase orders': {'page': '/purchase-orders', 'label': 'Purchase Orders'},
            'sales orders': {'page': '/sales-orders', 'label': 'Sales Orders'},
            'employees': {'page': '/employees', 'label': 'Employees'},
            'inventory': {'page': '/items', 'label': 'Inventory'},
            'settings': {'page': '/settings', 'label': 'Settings'},
        }
        for key, target in targets.items():
            if key in message.lower():
                return target
        return {'page': '/', 'label': 'Dashboard'}

    def _extract_actions_from_text(self, text: str) -> List[Dict]:
        """Extract suggested actions from AI response"""
        actions = []
        # Simple extraction - could be enhanced with NLP
        if 'create' in text.lower():
            actions.append({'type': 'create', 'label': 'Create new'})
        if 'approve' in text.lower():
            actions.append({'type': 'approve', 'label': 'Approve'})
        if 'review' in text.lower():
            actions.append({'type': 'review', 'label': 'Review'})
        return actions

    def _extract_navigation_from_actions(self, text: str) -> Dict:
        return {}

    def _determine_agent_type(self, message: str) -> str:
        if any(word in message.lower() for word in ['finance', 'invoice', 'budget', 'zakat', 'account']):
            return 'finance'
        elif any(word in message.lower() for word in ['hr', 'employee', 'payroll', 'leave', 'attendance']):
            return 'hr'
        elif any(word in message.lower() for word in ['inventory', 'stock', 'warehouse', 'supplier', 'purchase']):
            return 'supply_chain'
        return 'admin'


# ============================================================
# Workflow AI Generator - Natural Language to BPMN
# ============================================================

class WorkflowAIGenerator:
    """Converts natural language descriptions to BPMN workflows"""

    SYSTEM_PROMPT = """You are a BPMN Workflow Generator. Convert natural language business rules into structured BPMN workflow definitions.

Output format must be valid JSON with this structure:
{
    "name": "Workflow Name",
    "description": "Description",
    "nodes": [
        {
            "id": "node_1",
            "type": "startEvent|task|userTask|serviceTask|exclusiveGateway|parallelGateway|endEvent",
            "name": "Node Name",
            "x": 100,
            "y": 100,
            "properties": {}
        }
    ],
    "edges": [
        {
            "id": "edge_1",
            "source": "node_1",
            "target": "node_2",
            "name": "",
            "condition": ""
        }
    ],
    "state_machine_rules": [
        {
            "from_state": "draft",
            "to_state": "approved",
            "action": "approve",
            "guards": ["role:Manager,Admin"],
            "requires_approval": true
        }
    ],
    "permission_rules": [
        {
            "action": "approve",
            "roles": ["Manager", "Admin"],
            "condition": "amount <= 10000"
        }
    ]
}

Rules:
- Always include start and end events
- Use appropriate gateway types (XOR for decisions, AND for parallel)
- Include human approval nodes where specified
- Add service tasks for automated actions
- Generate corresponding state machine rules
- Generate permission rules based on thresholds
"""

    def __init__(self):
        self.llm = llm_core

    def generate_workflow(self, description: str, module: str = None) -> Dict:
        """Generate workflow from natural language description"""

        prompt = f"""Convert this business rule into a BPMN workflow:

"{description}"

Module: {module or 'general'}

Generate the complete workflow definition as JSON.
"""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=4000
        )

        try:
            workflow_def = json.loads(response['text'])
            workflow_def['source_description'] = description
            workflow_def['generated_at'] = datetime.now().isoformat()
            workflow_def['ai_generated'] = True
            return workflow_def
        except json.JSONDecodeError:
            # Fallback: return structured response
            return {
                'name': 'Generated Workflow',
                'description': description,
                'nodes': [
                    {'id': 'start', 'type': 'startEvent', 'name': 'Start', 'x': 100, 'y': 100},
                    {'id': 'task_1', 'type': 'userTask', 'name': 'Review', 'x': 250, 'y': 100},
                    {'id': 'end', 'type': 'endEvent', 'name': 'End', 'x': 400, 'y': 100}
                ],
                'edges': [
                    {'id': 'e1', 'source': 'start', 'target': 'task_1'},
                    {'id': 'e2', 'source': 'task_1', 'target': 'end'}
                ],
                'state_machine_rules': [],
                'permission_rules': [],
                'source_description': description,
                'generated_at': datetime.now().isoformat(),
                'ai_generated': True,
                'parse_error': True,
                'raw_response': response['text']
            }

    def generate_from_example(self, example_workflows: List[Dict], new_requirement: str) -> Dict:
        """Generate workflow based on examples"""
        examples_text = json.dumps(example_workflows, indent=2)

        prompt = f"""Given these example workflows:
{examples_text}

Generate a new workflow for:
"{new_requirement}"

Follow the same patterns and structure.
"""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=4000
        )

        try:
            return json.loads(response['text'])
        except:
            return {'error': 'Failed to parse workflow', 'raw': response['text']}

    def explain_workflow(self, workflow_json: Dict) -> str:
        """Generate human-readable explanation of a workflow"""
        prompt = f"""Explain this workflow in simple terms:
{json.dumps(workflow_json, indent=2)}

Provide:
1. Overall purpose
2. Step-by-step flow
3. Decision points
4. Approval requirements
5. Automation points
"""

        response = self.llm.generate(prompt=prompt)
        return response['text']

    def suggest_improvements(self, workflow_json: Dict) -> List[Dict]:
        """Suggest improvements to existing workflow"""
        prompt = f"""Analyze this workflow and suggest improvements:
{json.dumps(workflow_json, indent=2)}

Suggest:
1. Missing steps
2. Optimization opportunities
3. Automation candidates
4. Risk mitigation
5. Compliance checks

Return as JSON array of suggestions.
"""

        response = self.llm.generate(prompt=prompt)

        try:
            return json.loads(response['text'])
        except:
            return [{'suggestion': response['text'], 'type': 'general'}]


# Global instances
guidance_system = GuidanceSystem()
workflow_ai_generator = WorkflowAIGenerator()
