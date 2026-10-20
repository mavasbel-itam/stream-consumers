"""Credentials and settings: resolution in the factories, status, and the `.env` template."""

from __future__ import annotations

from pathlib import Path

import pytest

from stream_consumers.adapters.inbound.cli import OUTPUT_PASSWORD
from stream_consumers.adapters.outbound.providers.held_keys import HELD_KEYS, StaticHeldKeyCatalog
from stream_consumers.adapters.outbound.providers.registry import FactoryRegistry
from stream_consumers.adapters.outbound.providers.sources import FACTORIES
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.application.configuration_service import ConfigurationService
from stream_consumers.domain.errors import MissingCredentialError
from stream_consumers.domain.models import ConfigKind, Credential, HeldKey, Setting
from stream_consumers.ports.inbound import DescribeConfigurationUseCase
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies
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

    def test_a_minimum_window_is_not_negative(self) -> None:
        assert descriptor().min_window_s == 0.0 and descriptor(min_window_s=150.0).min_window_s == 150.0
        with pytest.raises(ValueError, match="min_window_s must not be negative"):
            descriptor(min_window_s=-1.0)


SPARE = HeldKey("pair", ("PAIR_SPARE_USER", "PAIR_SPARE_PASSWORD"), "Pair provider", "Second account.", "https://sign.up/pair")


def service(
    file_names: tuple[str, ...] = (), held: tuple[HeldKey, ...] = (), outputs: tuple[Credential, ...] = (), **env: str
) -> ConfigurationService:
    registry = FactoryRegistry([Plain(), Pair(), Optional(), SettingsOnly()], deps())
    return ConfigurationService(registry, FakeSecrets(env, file_names), StaticHeldKeyCatalog(held), outputs)


DB_PASSWORD = Credential(("OUT_PASSWORD",), "README.md#outputs", required=False, how_to_get="Password of a destination.")


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
        assert "Held keys" not in template

    def test_held_keys_are_listed_after_the_sources_and_never_reveal_values(self) -> None:
        configuration = service(held=(SPARE,), PAIR_SPARE_USER="spare-secret")
        rows = configuration.status()[-2:]
        assert [(r.source_id, r.env_var, r.kind, r.required, r.configured) for r in rows] == [
            ("pair", "PAIR_SPARE_USER", ConfigKind.HELD, False, True),
            ("pair", "PAIR_SPARE_PASSWORD", ConfigKind.HELD, False, False),
        ]
        assert rows[0].sign_up_url == "https://sign.up/pair" and rows[0].description == "Second account."
        template = configuration.env_template()
        assert "spare-secret" not in repr(rows) + template
        assert template.endswith(
            "# ===== Held keys: no source reads them; they are kept so each can be tested again\n"
            "# (tests/live/test_keys_live.py checks that each is accepted and that a damaged copy is refused).\n\n"
            "# --- pair: Pair provider. Second account.\n# Sign-up: https://sign.up/pair\nPAIR_SPARE_USER=\nPAIR_SPARE_PASSWORD=\n"
        )

    def test_output_credentials_come_between_the_sources_and_the_held_keys(self) -> None:
        configuration = service(held=(SPARE,), outputs=(DB_PASSWORD,), OUT_PASSWORD="db-secret")
        rows = configuration.status()
        assert [(r.source_id, r.env_var, r.kind, r.required, r.configured) for r in rows[-3:]] == [
            ("--out", "OUT_PASSWORD", ConfigKind.SECRET, False, True),
            ("pair", "PAIR_SPARE_USER", ConfigKind.HELD, False, False),
            ("pair", "PAIR_SPARE_PASSWORD", ConfigKind.HELD, False, False),
        ]
        assert (rows[-3].sign_up_url, rows[-3].description) == ("README.md#outputs", "Password of a destination.")
        template = configuration.env_template()
        assert "db-secret" not in repr(rows) + template
        assert (
            "# --- --out: credentials of output destinations (README.md#outputs)\n# How: Password of a destination.\nOUT_PASSWORD=\n\n"
            "# ===== Held keys" in template
        )
        assert service(("OUT_PASSWORD", "OTHER"), outputs=(DB_PASSWORD,)).unknown_variables() == ["OTHER"]

    def test_an_output_credential_must_not_be_a_source_variable_or_a_held_key(self) -> None:
        for name in ("PAIR_USER", "ONLY_SETTING", "PAIR_SPARE_USER"):
            with pytest.raises(ValueError, match=f"output credentials must not be variables a source reads or held keys: {name}"):
                service(held=(SPARE,), outputs=(Credential((name,), "u", required=False),))

    def test_a_held_key_must_not_be_a_variable_a_source_reads(self) -> None:
        for name in ("PAIR_USER", "PAIR_REGION"):
            with pytest.raises(ValueError, match=f"held keys must not be variables a source reads: {name}"):
                service(held=(HeldKey("pair", (name,), "p", "q", "u"),))


class TestUnknownVariables:
    def test_names_the_template_declares_are_known(self) -> None:
        names = ("PAIR_USER", "PAIR_PASSWORD", "PAIR_REGION", "OPT_ID", "OPT_SECRET", "ONLY_SETTING")
        assert service(names).unknown_variables() == []

    def test_a_name_no_source_reads_is_reported_in_file_order(self) -> None:
        assert service(("ZETA_KEY", "PAIR_USER", "ALPHA_KEY")).unknown_variables() == ["ZETA_KEY", "ALPHA_KEY"]

    def test_a_near_miss_is_still_unknown(self) -> None:
        assert service(("PAIR_USERS", "pair_user")).unknown_variables() == ["PAIR_USERS", "pair_user"]

    def test_the_process_environment_is_not_inspected(self) -> None:
        assert service((), UNRELATED="x").unknown_variables() == []

    def test_held_keys_are_known(self) -> None:
        names = ("PAIR_SPARE_USER", "PAIR_SPARE_PASSWORD", "OTHER")
        assert service(names, held=(SPARE,)).unknown_variables() == ["OTHER"]
        assert service(names).unknown_variables() == ["PAIR_SPARE_USER", "PAIR_SPARE_PASSWORD", "OTHER"]


class TestHeldKeys:
    def test_a_held_key_names_at_least_one_variable(self) -> None:
        with pytest.raises(ValueError, match="at least one environment variable"):
            HeldKey("x", (), "p", "q", "u")

    def test_a_catalog_names_each_variable_once(self) -> None:
        with pytest.raises(ValueError, match="held keys name a variable twice: A, B"):
            StaticHeldKeyCatalog((HeldKey("x", ("A", "B"), "p", "q", "u"), HeldKey("y", ("B", "A"), "p", "q", "u")))

    def test_the_default_catalog_is_every_held_key(self) -> None:
        assert StaticHeldKeyCatalog().held_keys() == HELD_KEYS


def test_env_example_is_the_generated_template() -> None:
    """`.env.example` must name exactly what the sources read; regenerate it with `stream-consumers keys --template`."""
    configuration = ConfigurationService(FactoryRegistry(FACTORIES, deps()), FakeSecrets(), StaticHeldKeyCatalog(), (OUTPUT_PASSWORD,))
    generated = configuration.env_template()
    assert (ROOT / ".env.example").read_text(encoding="utf-8") == generated


def test_env_example_defines_only_known_variables() -> None:
    from stream_consumers.adapters.outbound.system.environment import EnvSecretProvider

    example = EnvSecretProvider({}, ROOT / ".env.example")
    configuration = ConfigurationService(FactoryRegistry(FACTORIES, deps()), example, StaticHeldKeyCatalog(), (OUTPUT_PASSWORD,))
    assert example.file_names() and configuration.unknown_variables() == []


def test_every_declared_variable_is_unique_and_upper_case() -> None:
    names = [n for f in FACTORIES if f.descriptor.credential for n in f.descriptor.credential.env_vars]
    names += [s.env_var for f in FACTORIES for s in f.descriptor.settings]
    names += [n for k in HELD_KEYS for n in k.env_vars] + list(OUTPUT_PASSWORD.env_vars)
    assert len(names) == len(set(names)) and all(n.isupper() for n in names)
    assert {k.owner for k in HELD_KEYS} - {f.descriptor.id for f in FACTORIES} == set()  # every held key belongs to a known source
