"""
AI Services for Nexus SaaS
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal
from django.utils import timezone
from django.db.models import Avg, Sum, Count
from .models import AIModel, AIPrediction, AIAutomationRule, InventoryForecast, SmartAccountingSuggestion

logger = logging.getLogger(__name__)


class BaseAIService:
    """Base class for AI services"""

    def __init__(self, model: AIModel):
        self.model = model

    def predict(self, input_data: Dict) -> Dict:
        raise NotImplementedError

    def train(self, training_data: List[Dict]) -> bool:
        raise NotImplementedError


class OpenAIService(BaseAIService):
    """OpenAI API integration"""

    def __init__(self, model: AIModel):
        super().__init__(model)
        self.api_key = os.getenv(model.api_key_env or 'OPENAI_API_KEY')
        self.client = None
        if self.api_key:
            try:
                import openai
                openai.api_key = self.api_key
                self.client = openai
            except ImportError:
                logger.warning("openai package not installed")

    def predict(self, input_data: Dict) -> Dict:
        if not self.client:
            return {'error': 'OpenAI client not configured'}

        try:
            response = self.client.ChatCompletion.create(
                model=self.model.config.get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": self.model.config.get('system_prompt', '')},
                    {"role": "user", "content": json.dumps(input_data)}
                ],
                temperature=self.model.config.get('temperature', 0.7),
                max_tokens=self.model.config.get('max_tokens', 1000)
            )
            return {
                'output': response.choices[0].message.content,
                'confidence': 0.9,
                'tokens_used': response.usage.total_tokens
            }
        except Exception as e:
            logger.error(f"OpenAI prediction error: {e}")
            return {'error': str(e)}


class PredictiveInventoryService:
    """Predictive inventory management"""

    def __init__(self, tenant):
        self.tenant = tenant

    def forecast_demand(self, product_id: str, days_ahead: int = 30) -> List[Dict]:
        """Forecast demand for a product"""
        from apps.inventory.models import InventoryItem, InventoryMovement

        try:
            product = InventoryItem.objects.get(id=product_id, tenant=self.tenant)

            # Get historical data
            movements = InventoryMovement.objects.filter(
                product=product,
                movement_type='out',
                created_at__gte=timezone.now() - timezone.timedelta(days=365)
            ).order_by('created_at')

            # Simple moving average forecast (replace with ML model)
            daily_demand = {}
            for m in movements:
                day = m.created_at.date()
                daily_demand[day] = daily_demand.get(day, 0) + float(m.quantity)

            avg_demand = sum(daily_demand.values()) / len(daily_demand) if daily_demand else 0

            forecasts = []
            for i in range(days_ahead):
                date = timezone.now().date() + timezone.timedelta(days=i)
                predicted = avg_demand * (1 + 0.01 * i)  # Simple growth

                forecast = InventoryForecast.objects.create(
                    product=product,
                    forecast_date=date,
                    predicted_demand=Decimal(str(predicted)),
                    predicted_stock_level=Decimal(str(product.quantity - predicted)),
                    confidence_interval_lower=Decimal(str(predicted * 0.8)),
                    confidence_interval_upper=Decimal(str(predicted * 1.2)),
                )
                forecasts.append({
                    'date': date,
                    'predicted_demand': predicted,
                    'predicted_stock': float(product.quantity) - predicted
                })

            return forecasts

        except InventoryItem.DoesNotExist:
            return []

    def get_reorder_recommendations(self) -> List[Dict]:
        """Get AI-powered reorder recommendations"""
        from apps.inventory.models import InventoryItem

        products = InventoryItem.objects.filter(tenant=self.tenant)
        recommendations = []

        for product in products:
            # Check if stock is below reorder level
            if product.quantity <= product.reorder_level:
                # Get forecast
                latest_forecast = InventoryForecast.objects.filter(
                    product=product
                ).order_by('-forecast_date').first()

                recommended_qty = product.reorder_level * 2
                if latest_forecast:
                    recommended_qty = max(recommended_qty, float(latest_forecast.predicted_demand) * 7)

                recommendations.append({
                    'product_id': str(product.id),
                    'product_name': product.name,
                    'current_stock': float(product.quantity),
                    'reorder_level': float(product.reorder_level),
                    'recommended_quantity': recommended_qty,
                    'urgency': 'high' if product.quantity == 0 else 'medium',
                    'reason': 'Stock below reorder level'
                })

        return recommendations


class SmartAccountingService:
    """AI-powered smart accounting"""

    def __init__(self, tenant):
        self.tenant = tenant

    def categorize_transaction(self, transaction_data: Dict) -> Dict:
        """Auto-categorize a financial transaction"""

        # Simple rule-based categorization (replace with ML model)
        description = transaction_data.get('description', '').lower()
        amount = transaction_data.get('amount', 0)

        categories = {
            'rent': {'account': '6100', 'category': 'Operating Expenses', 'tags': ['rent', 'office']},
            'salary': {'account': '6200', 'category': 'Payroll', 'tags': ['salary', 'hr']},
            'utilities': {'account': '6300', 'category': 'Utilities', 'tags': ['electricity', 'water']},
            'supplies': {'account': '6400', 'category': 'Office Supplies', 'tags': ['supplies']},
            'marketing': {'account': '6500', 'category': 'Marketing', 'tags': ['ads', 'marketing']},
            'software': {'account': '6600', 'category': 'Software', 'tags': ['saas', 'software']},
        }

        best_match = None
        best_score = 0

        for keyword, category in categories.items():
            if keyword in description:
                score = len(keyword) / len(description) if description else 0
                if score > best_score:
                    best_score = score
                    best_match = category

        if not best_match:
            best_match = {'account': '6999', 'category': 'Miscellaneous', 'tags': []}

        suggestion = SmartAccountingSuggestion.objects.create(
            transaction_type=transaction_data.get('type', 'expense'),
            transaction_data=transaction_data,
            suggested_account=best_match['account'],
            suggested_category=best_match['category'],
            suggested_tags=best_match['tags'],
            confidence=min(best_score * 10, 0.95) if best_score > 0 else 0.5
        )

        return {
            'suggestion_id': str(suggestion.id),
            'account': best_match['account'],
            'category': best_match['category'],
            'tags': best_match['tags'],
            'confidence': suggestion.confidence
        }

    def detect_anomalies(self, days: int = 30) -> List[Dict]:
        """Detect anomalous transactions"""
        # Placeholder for anomaly detection
        return []


class AIAutomationEngine:
    """Execute AI automation rules"""

    def execute_rule(self, rule: AIAutomationRule, event_data: Dict):
        """Execute an automation rule"""
        if not rule.is_active:
            return

        # Check cooldown
        if rule.last_executed:
            cooldown = timezone.timedelta(minutes=rule.cooldown_minutes)
            if timezone.now() - rule.last_executed < cooldown:
                return

        # Check hourly limit
        recent_count = AIPrediction.objects.filter(
            model=rule.ai_model,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        ).count()

        if recent_count >= rule.max_executions_per_hour:
            logger.warning(f"Rule {rule.id} exceeded hourly execution limit")
            return

        # Execute AI model
        service = self._get_service(rule.ai_model)
        result = service.predict(event_data)

        # Store prediction
        prediction = AIPrediction.objects.create(
            model=rule.ai_model,
            input_data=event_data,
            output_data=result,
            confidence=result.get('confidence'),
            entity_type='automation_rule',
            entity_id=str(rule.id)
        )

        # Update rule stats
        rule.execution_count += 1
        rule.last_executed = timezone.now()
        rule.save()

        logger.info(f"Automation rule {rule.id} executed, prediction {prediction.id}")
        return prediction

    def _get_service(self, model: AIModel) -> BaseAIService:
        """Get appropriate service for model type"""
        if model.source_type == AIModel.SourceType.OPENAI:
            return OpenAIService(model)
        # Add more services as needed
        return OpenAIService(model)
