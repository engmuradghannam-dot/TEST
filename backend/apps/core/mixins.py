from rest_framework.exceptions import PermissionDenied


class CompanyScopedMixin:
    """
    Multi-tenant isolation mixin.

    Ensures a logged-in user can only read/write records that belong to
    their own company. Superusers bypass the restriction (needed for
    platform-level administration).

    Set `company_field` on the ViewSet to the lookup path from the model
    to its owning Company:
      - direct FK:            company_field = 'company'
      - one hop away:         company_field = 'branch__company'
      - nested line item:     company_field = 'purchase_order__company'

    If the model has no relation to Company at all (global/system config),
    do not use this mixin — restrict access with permission_classes instead.
    """
    company_field = 'company'

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user or not user.is_authenticated:
            return qs.none()
        if user.is_superuser:
            return qs
        if not getattr(user, 'company_id', None):
            # Authenticated user with no company assigned yet -> sees nothing,
            # instead of accidentally seeing every tenant's data.
            return qs.none()

        return qs.filter(**{self.company_field: user.company})

    def _resolve_company(self, validated_data):
        """Walk validated_data along company_field's path to find the
        Company instance implied by the incoming write, so we can block
        cross-tenant writes even on nested/line-item models."""
        parts = self.company_field.split('__')
        obj = validated_data.get(parts[0])
        for part in parts[1:]:
            if obj is None:
                return None
            obj = getattr(obj, part, None)
        return obj

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_superuser:
            company = self._resolve_company(serializer.validated_data)
            if company is not None and company != user.company:
                raise PermissionDenied("Cannot create records for another company.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if not user.is_superuser:
            # Block editing objects that already belong to another tenant.
            existing_company = self._get_instance_company(serializer.instance)
            if existing_company is not None and existing_company != user.company:
                raise PermissionDenied("Cannot modify records belonging to another company.")
        serializer.save()

    def _get_instance_company(self, instance):
        parts = self.company_field.split('__')
        obj = instance
        for part in parts:
            if obj is None:
                return None
            obj = getattr(obj, part, None)
        return obj
