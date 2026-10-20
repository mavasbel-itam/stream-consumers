"""A catalog holding the variable the outputs read (STREAM_CONSUMERS_OUTPUT_PASSWORD): `keys` must refuse it."""

from stream_consumers.domain.models import HeldKey
from tests.e2e.local_catalog import Local

FACTORIES = (Local("keyed"),)
HELD_KEYS = (
    HeldKey("keyed", ("STREAM_CONSUMERS_OUTPUT_PASSWORD",), "Local provider", "Same variable as the outputs.", "https://sign.up/e2e"),
)
