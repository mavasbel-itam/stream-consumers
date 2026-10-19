"""A catalog holding a key that one of its sources reads: `keys` must refuse it."""

from stream_consumers.domain.models import HeldKey
from tests.e2e.local_catalog import Local

FACTORIES = (Local("keyed"),)
HELD_KEYS = (HeldKey("keyed", ("E2E_KEY",), "Local provider", "Same variable as the source.", "https://sign.up/e2e"),)
