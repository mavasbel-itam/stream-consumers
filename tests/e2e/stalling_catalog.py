"""A catalog holding only the source that blocks the event loop on purpose. It is kept out of the
main catalog because a blocked loop freezes every source consumed beside it in the same run."""

from tests.e2e.local_catalog import Local

FACTORIES = (Local("stalling"),)
