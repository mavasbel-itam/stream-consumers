"""The hexagonal rules of this repository, checked on the source code itself."""

from __future__ import annotations

import ast
import dataclasses
import importlib
import inspect
import pkgutil
from abc import ABC
from pathlib import Path

import pytest
from cassandra.connection import EndPointFactory

import stream_consumers
from stream_consumers.ports import inbound
from stream_consumers.ports.outbound import outputs, providers, system

PACKAGE = Path(stream_consumers.__file__).parent


def modules(prefix: str) -> list[Path]:
    return sorted((PACKAGE / prefix).rglob("*.py"))


def imported(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


@pytest.mark.parametrize("path", modules("domain"), ids=lambda p: p.name)
def test_domain_depends_on_nothing_outside_the_domain(path: Path) -> None:
    internal = {m for m in imported(path) if m.startswith("stream_consumers")}
    assert all(m.startswith("stream_consumers.domain") for m in internal)


@pytest.mark.parametrize("path", modules("ports"), ids=lambda p: p.name)
def test_ports_depend_only_on_the_domain_and_ports(path: Path) -> None:
    internal = {m for m in imported(path) if m.startswith("stream_consumers")}
    assert all(m.startswith(("stream_consumers.domain", "stream_consumers.ports")) for m in internal)


@pytest.mark.parametrize("path", modules("application"), ids=lambda p: p.name)
def test_application_depends_only_on_the_domain_and_ports(path: Path) -> None:
    internal = {m for m in imported(path) if m.startswith("stream_consumers")}
    assert all(m.startswith(("stream_consumers.domain", "stream_consumers.ports")) for m in internal)


OUTBOUND = (providers, outputs, system)
"""The outbound port modules, by purpose: data providers, what the application writes, the operating system."""


def test_inbound_and_outbound_ports_are_split_and_abstract() -> None:
    for module in (inbound, *OUTBOUND):
        ports = [c for _, c in inspect.getmembers(module, inspect.isclass) if c.__module__ == module.__name__ and issubclass(c, ABC)]
        assert ports and all(inspect.isabstract(c) for c in ports)
    assert {c.__name__ for _, c in inspect.getmembers(inbound, inspect.isclass) if c.__module__ == inbound.__name__} == {
        "ListSourcesUseCase",
        "ConsumeStreamUseCase",
        "CheckSourcesUseCase",
        "SampleSourcesUseCase",
        "JudgeSamplingUseCase",
        "ProfileSourcesUseCase",
        "DescribeConfigurationUseCase",
    }


def test_only_the_composition_root_names_concrete_adapters_and_services() -> None:
    for path in PACKAGE.rglob("*.py"):
        if path.parent.name == "inbound" and path.name == "cli.py":
            continue
        services = {m for m in imported(path) if m.startswith("stream_consumers.application.")}
        assert not services or "application" in path.parts, path


def every_class() -> list[type]:
    found = []
    for info in pkgutil.walk_packages([str(PACKAGE)], "stream_consumers."):
        if info.name.endswith("__main__"):  # importing it runs the program
            continue
        module = importlib.import_module(info.name)
        found += [c for _, c in inspect.getmembers(module, inspect.isclass) if c.__module__ == module.__name__]
    return found


PORTS = tuple(
    c for m in (inbound, *OUTBOUND) for _, c in inspect.getmembers(m, inspect.isclass) if c.__module__ == m.__name__ and issubclass(c, ABC)
)


BEHAVIOUR = [
    c
    for c in every_class()
    if c.__module__.startswith(("stream_consumers.adapters", "stream_consumers.application")) and not dataclasses.is_dataclass(c)
]  # value objects (e.g. FileLocation) carry data, not behaviour


def test_the_behaviour_classes_were_found() -> None:
    assert len(BEHAVIOUR) > 100


LIBRARY_EXTENSIONS = {
    "stream_consumers.adapters.outbound.outputs.databases.PortMappedEndPointFactory": EndPointFactory,
}
"""Adapter-internal classes that plug into a client library through the library's own abstraction
instead of a port (the driver calls them, the application never does), each with that abstraction."""


def extends_a_port(cls: type) -> bool:
    library_base = LIBRARY_EXTENSIONS.get(f"{cls.__module__}.{cls.__qualname__}")
    return issubclass(cls, PORTS) or (library_base is not None and issubclass(cls, library_base))


@pytest.mark.parametrize("cls", BEHAVIOUR, ids=lambda c: f"{c.__module__.rsplit('.', 1)[-1]}.{c.__name__}")
def test_every_adapter_and_service_class_extends_a_port(cls: type) -> None:
    assert extends_a_port(cls), f"{cls.__qualname__} extends no port"


def test_a_library_extension_is_named_with_its_library_abstraction() -> None:
    found = {f"{c.__module__}.{c.__qualname__}" for c in BEHAVIOUR}
    assert set(LIBRARY_EXTENSIONS) <= found
    assert not any(issubclass(c, PORTS) for c in BEHAVIOUR if f"{c.__module__}.{c.__qualname__}" in LIBRARY_EXTENSIONS)


GROUPS = ("providers", "outputs", "system")
"""Each outbound adapter group, `adapters/outbound/<group>/`, implements the ports of `ports/outbound/<group>.py`."""


def test_the_outbound_adapters_are_grouped_like_their_ports() -> None:
    folder = PACKAGE / "adapters" / "outbound"
    assert sorted(p.name for p in folder.iterdir() if p.suffix == ".py") == ["__init__.py"]
    assert sorted(p.name for p in folder.iterdir() if p.is_dir() and p.name != "__pycache__") == sorted(GROUPS)


@pytest.mark.parametrize("group", GROUPS)
def test_an_outbound_adapter_group_never_imports_another_group(group: str) -> None:
    others = tuple(f"stream_consumers.adapters.outbound.{g}" for g in GROUPS if g != group)
    for path in modules(f"adapters/outbound/{group}"):
        assert not {m for m in imported(path) if m.startswith((*others, "stream_consumers.adapters.inbound"))}, path


@pytest.mark.parametrize("group", GROUPS)
def test_every_outbound_adapter_class_implements_a_port_of_its_own_group(group: str) -> None:
    own = tuple(c for c in PORTS if c.__module__ == f"stream_consumers.ports.outbound.{group}")
    classes = [c for c in BEHAVIOUR if c.__module__.startswith(f"stream_consumers.adapters.outbound.{group}.")]
    classes = [c for c in classes if f"{c.__module__}.{c.__qualname__}" not in LIBRARY_EXTENSIONS]
    assert classes and all(issubclass(c, own) for c in classes), [c.__qualname__ for c in classes if not issubclass(c, own)]


def test_the_provider_ports_and_the_output_ports_do_not_depend_on_each_other() -> None:
    assert "stream_consumers.ports.outbound.outputs" not in imported(Path(providers.__file__))
    assert "stream_consumers.ports.outbound.providers" not in imported(Path(outputs.__file__))
    assert not {m for m in imported(Path(system.__file__)) if m.startswith("stream_consumers.ports")}
