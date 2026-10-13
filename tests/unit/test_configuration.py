"""Credentials and settings: resolution in the factories, status, and the `.env` template."""

from __future__ import annotations

from pathlib import Path

import pytest

from stream_consumers.adapters.outbound.registry import FactoryRegistry
from stream_consumers.adapters.outbound.sources import FACTORIES
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.application.configuration_service import ConfigurationService
from stream_consumers.domain.errors import MissingCredentialError
from stream_consumers.domain.models import ConfigKind, Credential, Setting
from stream_consumers.ports.inbound import DescribeConfigurationUseCase
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies
from tests.support import FakeSecrets, ScriptedSource, deps, descriptor

ROOT = Path(__file__).resolve().parents[2]


class Pair(BaseSourceFactory):
    DESCRIPTOR = descriptor(
        "pair",
        credential=Credential(("PAIR_USER", "PAIR_PASSWORD"), "https://sign.up/pair", how_to_get="Form; answer by e-mail."),
        settings=(Setting("PAIR_REGION", "eu", "Region to read."),),
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [{"credentials": credentials, "region": self.setting(deps, "PAIR_REGION")}], deps.clock)  # type: ignore[arg-type]


class Optional(BaseSourceFactory):
    DESCRIPTOR = descriptor("optional", credential=Credential(("OPT_ID", "OPT_SECRET"), "https://sign.up/opt", required=False))

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [{"credentials": credentials}], deps.clock)  # type: ignore[arg-type]


class SettingsOnly(BaseSourceFactory):
    DESCRIPTOR = descriptor("settings", settings=(Setting("ONLY_SETTING", "", "Optional contact."),))

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [{"value": self.setting(deps, "ONLY_SETTING")}], deps.clock)  # type: ignore[arg-type]


class Plain(BaseSourceFactory):
    DESCRIPTOR = descriptor("plain")

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [{"credentials": credentials}], deps.clock)  # type: ignore[arg-type]


def payload(factory: BaseSourceFactory, **env: str) -> object:
    return factory.create(deps(secrets=env))._payloads[0]  # type: ignore[attr-defined]


class TestResolution:
    def test_every_required_variable_must_be_set(self) -> None:
        with pytest.raises(MissingCredentialError) as error:
            payload(Pair(), PAIR_USER="u")
        assert error.value.env_vars == ("PAIR_PASSWORD",) and error.value.sign_up_url == "https://sign.up/pair"

    def test_all_set_are_handed_over_with_settings(self) -> None:
        assert payload(Pair(), PAIR_USER="u", PAIR_PASSWORD="p") == {
            "credentials": {"PAIR_USER": "u", "PAIR_PASSWORD": "p"},
            "region": "eu",
        }
        assert payload(Pair(), PAIR_USER="u", PAIR_PASSWORD="p", PAIR_REGION="us")["region"] == "us"  # type: ignore[index]

    def test_optional_credentials_are_used_only_when_complete(self) -> None:
        assert payload(Optional()) == {"credentials": None}
        assert payload(Optional(), OPT_ID="i") == {"credentials": None}
        assert payload(Optional(), OPT_ID="i", OPT_SECRET="s") == {"credentials": {"OPT_ID": "i", "OPT_SECRET": "s"}}

    def test_no_credential(self) -> None:
        assert payload(Plain()) == {"credentials": None}

    def test_an_undeclared_setting_is_a_programming_error(self) -> None:
        with pytest.raises(KeyError, match="declares no setting NOPE"):
            Pair().setting(deps(), "NOPE")

    def test_a_credential_names_at_least_one_variable(self) -> None:
        with pytest.raises(ValueError):
            Credential((), "https://x")


def service(**env: str) -> ConfigurationService:
    return ConfigurationService(FactoryRegistry([Plain(), Pair(), Optional(), SettingsOnly()], deps()), FakeSecrets(env))


class TestConfigurationService:
    def test_is_the_inbound_port(self) -> None:
        assert isinstance(service(), DescribeConfigurationUseCase)

    def test_status_never_reveals_values(self) -> None:
        rows = service(PAIR_USER="secret-value", PAIR_REGION="us").status()
        assert [(r.source_id, r.env_var, r.kind, r.required, r.configured) for r in rows] == [
            ("optional", "OPT_ID", ConfigKind.SECRET, False, False),
            ("optional", "OPT_SECRET", ConfigKind.SECRET, False, False),
            ("pair", "PAIR_USER", ConfigKind.SECRET, True, True),
            ("pair", "PAIR_PASSWORD", ConfigKind.SECRET, True, False),
            ("pair", "PAIR_REGION", ConfigKind.SETTING, False, True),
            ("settings", "ONLY_SETTING", ConfigKind.SETTING, False, False),
        ]
        assert "secret-value" not in repr(rows)
        assert rows[2].sign_up_url == "https://sign.up/pair" and rows[2].description == "Form; answer by e-mail."
        assert rows[4].default == "eu"

    def test_template_lists_credentials_empty_and_settings_commented(self) -> None:
        template = service(PAIR_USER="secret-value").env_template()
        assert "secret-value" not in template
        assert (
            "# --- pair: Fake source (Tests)\n# Credentials REQUIRED. Sign-up: https://sign.up/pair\n# How: Form; answer by e-mail.\n"
            in template
        )
        assert "PAIR_USER=\nPAIR_PASSWORD=\n# Region to read. Default: eu\n# PAIR_REGION=eu\n" in template
        assert "# Credentials OPTIONAL (the source also works without it). Sign-up: https://sign.up/opt\nOPT_ID=\nOPT_SECRET=\n" in template
        assert "plain" not in template
        assert "# Optional contact. Default: (empty)\n# ONLY_SETTING=\n" in template


def test_env_example_is_the_generated_template() -> None:
    """`.env.example` must name exactly what the sources read; regenerate it with `stream-consumers keys --template`."""
    generated = ConfigurationService(FactoryRegistry(FACTORIES, deps()), FakeSecrets()).env_template()
    assert (ROOT / ".env.example").read_text(encoding="utf-8") == generated


def test_every_declared_variable_is_unique_and_upper_case() -> None:
    names = [n for f in FACTORIES if f.descriptor.credential for n in f.descriptor.credential.env_vars]
    names += [s.env_var for f in FACTORIES for s in f.descriptor.settings]
    assert len(names) == len(set(names)) and all(n.isupper() for n in names)
