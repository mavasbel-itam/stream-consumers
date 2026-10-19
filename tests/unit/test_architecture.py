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

import stream_consumers
from stream_consumers.ports import inbound, outbound

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


def test_inbound_and_outbound_ports_are_split_and_abstract() -> None:
    for module in (inbound, outbound):
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
    c for m in (inbound, outbound) for _, c in inspect.getmembers(m, inspect.isclass) if c.__module__ == m.__name__ and issubclass(c, ABC)
)


BEHAVIOUR = [
    c
    for c in every_class()
    if c.__module__.startswith(("stream_consumers.adapters", "stream_consumers.application")) and not dataclasses.is_dataclass(c)
]  # value objects (e.g. FileLocation) carry data, not behaviour


def test_the_behaviour_classes_were_found() -> None:
    assert len(BEHAVIOUR) > 100


@pytest.mark.parametrize("cls", BEHAVIOUR, ids=lambda c: f"{c.__module__.rsplit('.', 1)[-1]}.{c.__name__}")
def test_every_adapter_and_service_class_extends_a_port(cls: type) -> None:
    assert issubclass(cls, PORTS), f"{cls.__qualname__} extends no port"
