"""Every source against its real provider (Internet access required; never run in CI).

Run: uv run coverage run --rcfile=.coveragerc.live -m pytest tests/live -m live
All sources are consumed concurrently once (up to LIVE_SECONDS each); one test per source reads the result.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

import pytest
import pytest_asyncio

from stream_consumers.adapters.inbound.cli import USER_AGENT
from stream_consumers.adapters.outbound.http import AiohttpClient
from stream_consumers.adapters.outbound.registry import FactoryRegistry
from stream_consumers.adapters.outbound.sinks import NullEventSink
from stream_consumers.adapters.outbound.sources import FACTORIES
from stream_consumers.adapters.outbound.system import EnvSecretProvider, SystemClock
from stream_consumers.application.check_service import CheckService
from stream_consumers.application.consume_service import ConsumeService
from stream_consumers.domain.models import RunReport, RunStatus
from stream_consumers.ports.outbound import SourceDependencies
from tests.support import MemoryReports

pytestmark = pytest.mark.live
SECONDS = float(os.environ.get("LIVE_SECONDS", "60"))


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def results() -> Mapping[str, RunReport]:
    clock = SystemClock()
    http = AiohttpClient(USER_AGENT)
    deps = SourceDependencies(http, EnvSecretProvider(os.environ, Path(".env")), clock, USER_AGENT)
    try:
        registry = FactoryRegistry(FACTORIES, deps)
        service = CheckService(ConsumeService(registry, clock), NullEventSink(), MemoryReports(), concurrency=len(FACTORIES))
        reports = await service.check([f.descriptor.id for f in FACTORIES], SECONDS)
    finally:
        await http.close()
    return {r.source_id: r for r in reports}


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("source_id", sorted(f.descriptor.id for f in FACTORIES))
async def test_source_delivers_events(results: Mapping[str, RunReport], source_id: str) -> None:
    report = results[source_id]
    assert report.status in (RunStatus.OK, RunStatus.KEY_PENDING), f"{report.status.value}: {report.detail}"
    if report.status is RunStatus.OK:
        assert report.events >= 1 and report.attributes_median >= 1
