from __future__ import annotations

from core.models import Analysis, Conversation


def get_or_create_default_conversation(analysis: Analysis) -> Conversation:
    """Return the oldest conversation for this analysis, or create one."""
    conv = Conversation.objects.filter(analysis=analysis).order_by("created_at").first()
    if conv is None:
        conv = Conversation.objects.create(analysis=analysis)
    return conv


def resolve_conversation(analysis: Analysis, conversation_id: str | None) -> Conversation:
    """Use a valid conversation_id for this analysis, otherwise the default."""
    if conversation_id:
        found = Conversation.objects.filter(id=conversation_id, analysis=analysis).first()
        if found is not None:
            return found
    return get_or_create_default_conversation(analysis)
