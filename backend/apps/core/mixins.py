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

    def initial(self, request, *args, **kwargs):
        # Runs before every action (list/create/retrieve/update/delete) —
        # stashes the authenticated user so the audit-log signal handlers
        # (which have no access to the request) can attribute changes.
        super().initial(request, *args, **kwargs)
        from .threadlocal import set_current_user
        set_current_user(request.user if request.user and request.user.is_authenticated else None)
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


class LockAfterSubmitMixin:
    """
    Prevents editing/deleting a document once its parent transaction has left
    Draft status. Attach to line-item ViewSets (PO items, tax charges,
    payments, etc.) that hang off a parent document with a `status` field.

    Set:
      - parent_field: attribute name on the instance/serializer pointing to
                       the parent document (e.g. 'purchase_order').
      - draft_statuses: set of parent statuses in which edits are still
                        allowed (default: {'Draft'}).
    """
    parent_field = None
    draft_statuses = {'Draft'}

    def _get_parent(self, validated_data=None, instance=None):
        if instance is not None:
            return getattr(instance, self.parent_field, None)
        if validated_data is not None:
            return validated_data.get(self.parent_field)
        return None

    def _assert_editable(self, parent):
        if parent is not None and getattr(parent, 'status', None) not in self.draft_statuses:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                f"Cannot modify this line — the parent document is already '{parent.status}'. "
                "Only Draft documents can be edited."
            )

    def perform_create(self, serializer):
        parent = self._get_parent(validated_data=serializer.validated_data)
        self._assert_editable(parent)
        super().perform_create(serializer)

    def perform_update(self, serializer):
        parent = self._get_parent(instance=serializer.instance)
        self._assert_editable(parent)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        parent = self._get_parent(instance=instance)
        self._assert_editable(parent)
        super().perform_destroy(instance)


class AuditUserMixin:
    """Standalone version of the user-stashing hook in CompanyScopedMixin,
    for the handful of ViewSets that aren't company-scoped (e.g. Company
    itself, system-wide Module catalog, Workflow definitions) but still
    need their changes attributed in the audit log."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        from .threadlocal import set_current_user
        set_current_user(request.user if request.user and request.user.is_authenticated else None)


class BranchScopedMixin:
    """Row-level security one level below company: restricts the queryset
    to the user's branch unless the user has the `<app>.view_all_branches`
    permission or is a company admin. Stack AFTER CompanyScopedMixin:

        class JournalEntryViewSet(CompanyScopedMixin, BranchScopedMixin, ...)
    """

    branch_field = 'branch'

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        model = qs.model
        perm = f"{model._meta.app_label}.view_all_branches"
        if user.is_superuser or user.has_perm(perm):
            return qs
        user_branch_id = getattr(user, 'branch_id', None)
        if user_branch_id and self.branch_field in [
                f.name for f in model._meta.fields]:
            return qs.filter(**{f"{self.branch_field}_id": user_branch_id})
        return qs


def user_effective_permissions(user):
    """Permission inheritance resolver: direct perms + group perms +
    role-implied perms, deduplicated. Single source of truth for
    'what can this user actually do'."""
    if user.is_superuser:
        from django.contrib.auth.models import Permission
        return set(Permission.objects.values_list('codename', flat=True))
    perms = set(user.user_permissions.values_list('codename', flat=True))
    perms |= set(user.groups.values_list('permissions__codename', flat=True))
    perms.discard(None)
    return perms
