"""A catalog listing one source twice: the registry must refuse it."""

from tests.e2e.local_catalog import Local

FACTORIES = (Local("ws_ok"), Local("ws_ok"))
