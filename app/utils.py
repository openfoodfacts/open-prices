import logging

import sentry_sdk
from sentry_sdk.integrations import Integration
from sentry_sdk.integrations.logging import LoggingIntegration


def init_sentry(sentry_dsn: str | None, integrations: list[Integration] | None = None):
    if sentry_dsn:
        integrations = integrations or []
        integrations.append(
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.WARNING,  # Send warning and errors as events
            )
        )
        sentry_sdk.init(  # type:ignore  # mypy say it's abstract
            sentry_dsn,
            integrations=integrations,
        )
