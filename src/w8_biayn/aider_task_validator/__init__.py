"""Deterministic Aider C++ SFT projection and admission tooling."""

from .projector import project_manifest
from .validator import audit_v1, consumer_verify, validate_dataset, validate_v2

__all__ = ["audit_v1", "consumer_verify", "project_manifest", "validate_dataset", "validate_v2"]
