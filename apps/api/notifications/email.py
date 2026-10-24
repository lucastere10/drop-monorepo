from __future__ import annotations

import logging
from typing import Protocol

from django.conf import settings

logger = logging.getLogger(__name__)


class EmailBackend(Protocol):
    def send(self, *, to: str, subject: str, html: str, text: str = "") -> None: ...


class ConsoleEmailBackend:
    def send(self, *, to: str, subject: str, html: str, text: str = "") -> None:
        logger.info("EMAIL to=%s subject=%s\n%s", to, subject, text or html)


class ResendEmailBackend:
    def send(self, *, to: str, subject: str, html: str, text: str = "") -> None:
        import resend

        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send(
            {
                "from": settings.EMAIL_FROM,
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text or None,
            }
        )


def get_email_backend() -> EmailBackend:
    kind = settings.EMAIL_BACKEND_KIND
    if kind == "resend":
        return ResendEmailBackend()
    return ConsoleEmailBackend()
