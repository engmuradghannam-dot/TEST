from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError


def validate_transition(transitions, current_status, new_status):
    """
    Raise a DRF ValidationError if moving from current_status to new_status
    isn't an allowed edge in the given transition map.

    transitions: dict[str, set[str]] mapping each status to the set of
                 statuses it's allowed to move to next.
    """
    if current_status == new_status:
        return
    allowed = transitions.get(current_status, set())
    if new_status not in allowed:
        raise ValidationError(
            f"Cannot change status from '{current_status}' to '{new_status}'. "
            f"Allowed next steps: {sorted(allowed) or 'none — this is a final state'}."
        )


def run_side_effect(callable_fn):
    """Runs a model method that may raise django.core.exceptions.ValidationError
    (used for cross-app business logic like stock movements) and re-raises it
    as a DRF ValidationError so it surfaces as a clean 400 response."""
    try:
        callable_fn()
    except DjangoValidationError as e:
        raise ValidationError(e.messages if hasattr(e, 'messages') else str(e))
