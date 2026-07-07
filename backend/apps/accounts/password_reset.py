"""Password reset endpoints (token-based, no extra dependencies)."""
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


TOKEN_TTL = 3600  # 1 hour


class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            cache.set(f'pwd_reset:{token}', user.pk, TOKEN_TTL)
            reset_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')}/reset-password?token={token}"
            try:
                send_mail(
                    subject='Reset your Nexus password',
                    message=f'Click here to reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour.',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@nexus.erp'),
                    recipient_list=[email],
                    fail_silently=True,
                )
            except Exception:
                pass
        # Always return 200 to prevent email enumeration
        return Response({'message': 'If that email exists, a reset link has been sent.'})


class ConfirmPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token', '')
        new_password = request.data.get('new_password', '')
        if not token or not new_password:
            return Response({'error': 'token and new_password are required'}, status=400)
        if len(new_password) < 8:
            return Response({'error': 'Password must be at least 8 characters'}, status=400)
        user_pk = cache.get(f'pwd_reset:{token}')
        if not user_pk:
            return Response({'error': 'Invalid or expired token'}, status=400)
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_pk)
            user.set_password(new_password)
            user.save(update_fields=['password'])
            cache.delete(f'pwd_reset:{token}')
            return Response({'message': 'Password reset successfully'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=400)
