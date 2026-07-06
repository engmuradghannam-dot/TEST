"""
AI Brain Layer for Nexus CE-ERP OS
Components: LLM Core, RAG Memory System, Context Engine
"""
import os
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

logger = logging.getLogger(__name__)


# ============================================================
# LLM Core - Multi-Provider AI Adapter
# ============================================================

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    RULE_BASED = "rule_based"


class LLMCore:
    """Central LLM orchestrator supporting multiple providers"""

    def __init__(self, default_provider: LLMProvider = None):
        self.default_provider = default_provider or LLMProvider.OPENAI
        self._clients = {}
        self._initialize_clients()

    def _initialize_clients(self):
        # OpenAI
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                import openai
                self._clients[LLMProvider.OPENAI] = openai.OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

        # Anthropic
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            try:
                import anthropic
                self._clients[LLMProvider.ANTHROPIC] = anthropic.Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")

        # Google
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                self._clients[LLMProvider.GOOGLE] = genai
                logger.info("Google AI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google AI: {e}")

    def generate(self, prompt: str, system_prompt: str = None, 
                 provider: LLMProvider = None, model: str = None,
                 temperature: float = 0.7, max_tokens: int = 2000,
                 context: List[Dict] = None) -> Dict[str, Any]:
        """Generate text using specified provider"""
        provider = provider or self.default_provider

        if provider == LLMProvider.RULE_BASED:
            return self._rule_based_response(prompt, context)

        client = self._clients.get(provider)
        if not client:
            logger.warning(f"Provider {provider} not available, falling back to rule-based")
            return self._rule_based_response(prompt, context)

        try:
            if provider == LLMProvider.OPENAI:
                return self._openai_generate(client, prompt, system_prompt, model, temperature, max_tokens, context)
            elif provider == LLMProvider.ANTHROPIC:
                return self._anthropic_generate(client, prompt, system_prompt, model, temperature, max_tokens, context)
            elif provider == LLMProvider.GOOGLE:
                return self._google_generate(client, prompt, system_prompt, model, temperature, max_tokens, context)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._rule_based_response(prompt, context)

    def _openai_generate(self, client, prompt, system_prompt, model, temperature, max_tokens, context):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            for msg in context:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model or "gpt-4.1",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return {
            'text': response.choices[0].message.content,
            'provider': 'openai',
            'model': model or "gpt-4.1",
            'tokens_used': response.usage.total_tokens if response.usage else 0,
            'finish_reason': response.choices[0].finish_reason
        }

    def _anthropic_generate(self, client, prompt, system_prompt, model, temperature, max_tokens, context):
        messages = []
        if context:
            for msg in context:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        response = client.messages.create(
            model=model or "claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=messages
        )
        return {
            'text': response.content[0].text,
            'provider': 'anthropic',
            'model': model or "claude-3-5-sonnet",
            'tokens_used': response.usage.input_tokens + response.usage.output_tokens if response.usage else 0,
            'finish_reason': response.stop_reason
        }

    def _google_generate(self, client, prompt, system_prompt, model, temperature, max_tokens, context):
        model_name = model or "gemini-1.5-pro"
        gemini_model = client.GenerativeModel(model_name)

        chat = gemini_model.start_chat(history=[])
        if system_prompt:
            chat.send_message(f"System: {system_prompt}")
        if context:
            for msg in context:
                chat.send_message(msg.get("content", ""))

        response = chat.send_message(prompt)
        return {
            'text': response.text,
            'provider': 'google',
            'model': model_name,
            'tokens_used': 0,
            'finish_reason': 'stop'
        }

    def _rule_based_response(self, prompt: str, context: List[Dict] = None) -> Dict:
        """Fallback rule-based response"""
        return {
            'text': "I understand your request. However, the AI service is currently unavailable. Please try again later or contact support.",
            'provider': 'rule_based',
            'model': 'fallback',
            'tokens_used': 0,
            'finish_reason': 'fallback'
        }

    def embed(self, text: str, provider: LLMProvider = None) -> List[float]:
        """Generate embeddings for text"""
        provider = provider or LLMProvider.OPENAI
        client = self._clients.get(provider)

        if provider == LLMProvider.OPENAI and client:
            try:
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Embedding failed: {e}")

        # Fallback: simple hash-based embedding
        return self._simple_embedding(text)

    def _simple_embedding(self, text: str) -> List[float]:
        """Simple deterministic embedding fallback"""
        hash_val = hashlib.md5(text.encode()).hexdigest()
        vec = [int(hash_val[i:i+2], 16) / 255.0 for i in range(0, 64, 2)]
        return vec + [0.0] * (384 - len(vec))  # Pad to 384 dims


# ============================================================
# RAG Memory System - Vector Database Integration
# ============================================================

class RAGMemory:
    """Retrieval-Augmented Generation Memory System"""

    def __init__(self, llm_core: LLMCore = None):
        self.llm = llm_core or LLMCore()
        self._vector_store = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        try:
            import chromadb
            self._vector_store = chromadb.Client(
                chromadb.Settings(
                    persist_directory=os.path.join(settings.BASE_DIR, "vector_db"),
                    anonymized_telemetry=False
                )
            )
            # Create collections for different data types
            for collection_name in ["company_knowledge", "documents", "conversations", "code_knowledge"]:
                try:
                    self._vector_store.get_collection(collection_name)
                except:
                    self._vector_store.create_collection(collection_name)
            logger.info("Vector store initialized")
        except Exception as e:
            logger.warning(f"Vector store initialization failed: {e}")
            self._vector_store = None

    def add_document(self, collection: str, doc_id: str, text: str, 
                     metadata: Dict = None, tenant_id: str = None):
        """Add document to vector store"""
        if not self._vector_store:
            return False

        try:
            embedding = self.llm.embed(text)
            coll = self._vector_store.get_collection(collection)
            meta = metadata or {}
            if tenant_id:
                meta['tenant_id'] = tenant_id
            coll.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[meta]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False

    def query(self, collection: str, query_text: str, 
              tenant_id: str = None, n_results: int = 5) -> List[Dict]:
        """Query similar documents from vector store"""
        if not self._vector_store:
            return []

        try:
            embedding = self.llm.embed(query_text)
            coll = self._vector_store.get_collection(collection)

            where_filter = None
            if tenant_id:
                where_filter = {"tenant_id": tenant_id}

            results = coll.query(
                query_embeddings=[embedding],
                n_results=n_results,
                where=where_filter
            )

            documents = []
            for i in range(len(results['ids'][0])):
                documents.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i] if results['documents'] else '',
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })
            return documents
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def generate_with_context(self, query: str, collection: str = "company_knowledge",
                              tenant_id: str = None, system_prompt: str = None) -> Dict:
        """RAG: Retrieve relevant docs and generate answer"""
        # Retrieve context
        relevant_docs = self.query(collection, query, tenant_id=tenant_id, n_results=5)

        # Build context string
        context_text = "\n\n".join([
            f"Document {i+1}: {doc['text']}"
            for i, doc in enumerate(relevant_docs)
        ])

        # Build prompt
        full_prompt = f"""Based on the following context, answer the question:

Context:
{context_text}

Question: {query}

Answer:"""

        # Generate
        response = self.llm.generate(
            prompt=full_prompt,
            system_prompt=system_prompt or "You are an AI assistant for an ERP system. Use the provided context to answer accurately."
        )

        response['sources'] = relevant_docs
        return response


# ============================================================
# Context Engine - User/Company/Operation Context
# ============================================================

@dataclass
class UserContext:
    user_id: str
    email: str
    role: str
    company_id: str
    branch_id: Optional[str] = None
    department_id: Optional[str] = None
    permissions: List[str] = None
    language: str = "ar"
    timezone: str = "Asia/Riyadh"

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'email': self.email,
            'role': self.role,
            'company_id': self.company_id,
            'branch_id': self.branch_id,
            'department_id': self.department_id,
            'permissions': self.permissions or [],
            'language': self.language,
            'timezone': self.timezone
        }


@dataclass
class CompanyContext:
    company_id: str
    name: str
    industry: str
    size: str
    modules_enabled: List[str] = None
    custom_settings: Dict = None


class ContextEngine:
    """Manages context for AI operations"""

    def __init__(self):
        self._cache = {}

    def build_user_context(self, user) -> UserContext:
        """Build context from Django user object"""
        return UserContext(
            user_id=str(user.id),
            email=user.email,
            role=getattr(user, 'role', 'User'),
            company_id=str(getattr(user, 'company_id', '')),
            branch_id=str(getattr(user, 'branch_id', '')) if getattr(user, 'branch_id', None) else None,
            department_id=str(getattr(user, 'department_id', '')) if getattr(user, 'department_id', None) else None,
            permissions=list(user.user_permissions.values_list('codename', flat=True)),
            language=getattr(user, 'language', 'ar'),
            timezone=getattr(user, 'time_zone', 'Asia/Riyadh')
        )

    def build_company_context(self, company) -> CompanyContext:
        """Build context from Company model"""
        return CompanyContext(
            company_id=str(company.id),
            name=company.name,
            industry=getattr(company, 'industry', ''),
            size=getattr(company, 'size', 'small'),
            modules_enabled=getattr(company, 'modules_enabled', []),
            custom_settings=getattr(company, 'settings', {})
        )

    def build_system_context(self, user_context: UserContext, 
                           company_context: CompanyContext = None) -> str:
        """Build system context prompt for AI"""
        ctx = f"""You are an AI assistant for an ERP system. 

User Context:
- Role: {user_context.role}
- Company: {company_context.name if company_context else 'Unknown'}
- Language: {user_context.language}
- Timezone: {user_context.timezone}

Guidelines:
- Respond in {user_context.language} (Arabic or English)
- Consider user's role permissions when suggesting actions
- Provide actionable ERP-specific advice
- Be concise but thorough
"""
        return ctx

    def get_module_context(self, module_name: str) -> str:
        """Get context about a specific ERP module"""
        contexts = {
            'accounts': "Financial accounting module: GL, AP, AR, journals, financial reports",
            'inventory': "Inventory module: stock management, warehouses, reorder points, transfers",
            'buying': "Purchasing module: POs, suppliers, RFQs, procurement",
            'selling': "Sales module: SOs, customers, quotations, deliveries",
            'hr': "HR module: employees, payroll, leave, attendance, recruitment",
            'crm': "CRM module: leads, opportunities, customers, communications",
            'projects': "Project module: tasks, Gantt, time tracking, budgets",
            'manufacturing': "Manufacturing module: BOM, work orders, production",
            'assets': "Asset module: fixed assets, depreciation, maintenance",
            'workflow': "Workflow module: BPMN, approvals, state machines, automation"
        }
        return contexts.get(module_name, f"{module_name} module")


# ============================================================
# AI Models
# ============================================================

class AIConversation(models.Model):
    """Persistent AI conversation history"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.CharField(max_length=200, blank=True)
    module = models.CharField(max_length=50, blank=True)
    messages = models.JSONField(default=list)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']

    def add_message(self, role: str, content: str, metadata: Dict = None):
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
        self.save()

    def get_context_messages(self, limit: int = 10) -> List[Dict]:
        return self.messages[-limit:]


class AIPromptTemplate(models.Model):
    """Reusable AI prompt templates"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    system_prompt = models.TextField()
    user_prompt_template = models.TextField()
    variables = models.JSONField(default=list, help_text="List of required variables")
    module = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def render(self, variables: Dict) -> Tuple[str, str]:
        """Render system and user prompts with variables"""
        sys_prompt = self.system_prompt
        user_prompt = self.user_prompt_template

        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            sys_prompt = sys_prompt.replace(placeholder, str(value))
            user_prompt = user_prompt.replace(placeholder, str(value))

        return sys_prompt, user_prompt


class AIKnowledgeBase(models.Model):
    """Company knowledge base entries for RAG"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='ai_knowledge')
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, blank=True)
    tags = models.JSONField(default=list)
    source = models.CharField(max_length=100, blank=True)
    embedding_id = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['company', 'category']),
            models.Index(fields=['company', 'tags']),
        ]


# Global instances
llm_core = LLMCore()
rag_memory = RAGMemory(llm_core)
context_engine = ContextEngine()
