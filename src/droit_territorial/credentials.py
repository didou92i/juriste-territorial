"""Opt-in OS secret storage. No plaintext fallback, MCP input or secret in argv."""

import getpass
import json
import os
import sys
import warnings

from .models import SourceError

FIELDS = {
    "piste": ("PISTE_CLIENT_ID", "PISTE_CLIENT_SECRET"),
    "judilibre": ("JUDILIBRE_KEY_ID",),
}


def secure_backend():
    # Instantiate only native, secure backends: never discover third-party plaintext stores.
    try:
        if sys.platform == "darwin":
            from keyring.backends.macOS import Keyring
        elif sys.platform == "win32":
            from keyring.backends.Windows import WinVaultKeyring as Keyring
        else:
            from keyring.backends.SecretService import Keyring
        return Keyring()
    except Exception:
        raise SourceError(
            "credential_store_unavailable",
            "Installer l'option credentials et déverrouiller le trousseau système, "
            "ou utiliser les variables du gestionnaire de secrets de l'hébergeur.",
        ) from None


def store_name(provider, environment):
    if provider not in FIELDS or environment not in {"production", "sandbox"}:
        raise SourceError("invalid_configuration", "Profil d'identifiants non reconnu")
    return f"juriste-territorial.{provider}.{environment}"


def read_profile(provider, environment):
    name = store_name(provider, environment)
    try:
        raw = secure_backend().get_password(name, "credentials")
        if raw is None:
            return {}
        if len(raw) > 16000:
            raise ValueError
        value = json.loads(raw)
        if not isinstance(value, dict) or set(value) != set(FIELDS[provider]):
            raise ValueError
        if not all(isinstance(x, str) and x.strip() for x in value.values()):
            raise ValueError
        return value
    except (ValueError, TypeError):
        raise SourceError(
            "credential_store_invalid", "Profil incomplet : relancer configure dans un terminal"
        ) from None
    except SourceError:
        raise
    except Exception:
        raise SourceError(
            "credential_store_unavailable", "Le trousseau système est indisponible ou verrouillé"
        ) from None


def load_credentials(environment):
    mode = os.getenv("JT_CREDENTIAL_STORE", "environment")
    if mode not in {"environment", "keyring"}:
        raise SourceError("invalid_configuration", "JT_CREDENTIAL_STORE: environment ou keyring")
    values, issues = {}, []
    for provider, fields in FIELDS.items():
        # An explicitly supplied environment profile wins as a whole, even if incomplete.
        # Never combine two OAuth credentials from different profiles.
        if any(key in os.environ for key in fields):
            values.update({key: os.getenv(key, "") for key in fields})
        elif mode == "keyring":
            try:
                values.update(read_profile(provider, environment))
            except SourceError as exc:
                issues.append({"provider": provider, "code": exc.problem.code})
    return values, tuple(issues)


def configure(provider, environment):
    """Interactive operator-only write, outside the read-only MCP surface."""
    name = store_name(provider, environment)
    if not sys.stdin.isatty():
        raise SourceError(
            "interactive_terminal_required", "Lancer configure dans votre terminal local"
        )
    backend = secure_backend()
    values = {}
    # Refuse getpass's echoing fallback if the terminal cannot hide input.
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        for key in FIELDS[provider]:
            try:
                value = getpass.getpass(f"{key} (saisie masquée) : ").strip()
            except (getpass.GetPassWarning, EOFError, KeyboardInterrupt):
                raise SourceError(
                    "input_cancelled", "Saisie interrompue ; rien enregistré"
                ) from None
            if not value or len(value) > 8000:
                raise SourceError(
                    "invalid_input", "Identifiant vide ou trop long ; rien enregistré"
                )
            values[key] = value
    try:
        encoded = json.dumps(values)
        backend.set_password(name, "credentials", encoded)
        if backend.get_password(name, "credentials") != encoded:
            raise RuntimeError
    except Exception:
        raise SourceError(
            "credential_store_write_failed", "Enregistrement dans le trousseau non confirmé"
        ) from None
    return {
        "status": "stored_not_probed",
        "provider": provider,
        "environment": environment,
        "next_step": "Configurer JT_CREDENTIAL_STORE=keyring et PISTE_ENV dans le processus MCP, "
        "redémarrer le MCP, puis appeler get_source_status avec probe=true.",
    }
