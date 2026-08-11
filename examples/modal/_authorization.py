"""Fail-closed authorization gate for every legacy Modal entrypoint."""

from __future__ import annotations

import os
import sys


AUTHORIZATION_ENV = "GLM47_MODAL_FULL_AUTHORIZATION"
AUTHORIZATION_PHRASE = "I_FULLY_AUTHORIZE_MODAL_EXECUTION_AND_COSTS"
WARNING = (
    "MODAL EXECUTION BLOCKED: You have accidentally started a Modal run, which "
    "is not authorized. Continue only after explicit full authorization by setting "
    f"{AUTHORIZATION_ENV}={AUTHORIZATION_PHRASE}."
)


def require_full_modal_authorization() -> None:
    """Stop before importing the Modal SDK unless the exact approval is present."""

    if os.environ.get(AUTHORIZATION_ENV) != AUTHORIZATION_PHRASE:
        print(WARNING, file=sys.stderr)
        raise SystemExit(64)
