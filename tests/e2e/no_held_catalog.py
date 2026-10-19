"""A catalog without held keys: the template has no held-keys block."""

from tests.e2e.local_catalog import Local

FACTORIES = (Local("keyed"),)
