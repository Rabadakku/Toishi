"""Shared fixtures for the engine tests: a profile with a small calculus pack (see
test_service.py) and its fixed clock."""

from tests.engine.test_service import clock, storage

__all__ = ["clock", "storage"]
