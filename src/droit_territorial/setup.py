"""Portable first-use guidance and explicit, bounded connection diagnostics."""

from datetime import UTC, date, datetime

from .models import SourceError


def setup_status(settings):
    missing = [
        key
        for key, value in (
            ("PISTE_CLIENT_ID", settings.client_id),
            ("PISTE_CLIENT_SECRET", settings.client_secret),
        )
        if not value
    ]
    return {
        "legifrance": {
            "state": "configuration_required" if missing else "configured_not_verified",
            "missing_variables": missing,
            "purpose": "Codes, textes, JORF et jurisprudence accessible via Légifrance",
        },
        "judilibre": {
            "optional": True,
            "state": "configured_not_verified"
            if settings.oauth_configured or settings.judilibre_key
            else "not_configured",
            "purpose": "Jurisprudence judiciaire ; inutile pour l'index administratif CE/CAA/TA",
            "credentials": "JUDILIBRE_KEY_ID ou application OAuth PISTE abonnée à JudiLibre",
        },
        "environment": "sandbox" if settings.sandbox else "production",
        "credential_store_issues": list(settings.credential_issues),
        "guide_topic": "installation",
        "portal": "https://piste.gouv.fr/",
        "official_help": "https://www.legifrance.gouv.fr/contenu/pied-de-page/foire-aux-questions-api",
        "local_setup_command": "uv run --extra credentials droit-territorial configure piste",
        "verification": "get_source_status(source_id='legifrance', probe=true)",
        "without_api_keys": [
            "methodology",
            "rules",
            "official_page_reader",
            "configured_local_indexes",
        ],
        "assistant_guidance": "Au premier échange, signaler brièvement les accès manquants utiles "
        "au dossier et proposer le guide installation. Continuer avec les capacités disponibles. "
        "Ne pas répéter la demande à chaque appel. Ne jamais demander les clés dans le chat, "
        "un outil MCP, un fichier Git ou une commande contenant leurs valeurs.",
    }


async def probe_connection(service, provider):
    if provider not in {"legifrance", "judilibre"}:
        raise SourceError("unsupported_probe", "Le diagnostic API couvre Légifrance ou JudiLibre")
    configured = service.settings.oauth_configured or (
        provider == "judilibre" and bool(service.settings.judilibre_key)
    )
    report = {
        "provider": provider,
        "at": datetime.now(UTC).isoformat(),
        "environment": "sandbox" if service.settings.sandbox else "production",
        "checks": [],
        "scope": "Recherche et lecture ponctuelles ; ni validation juridique ni recette historique complète",
    }
    if not configured:
        return {**report, "state": "not_run", "reason": "credentials_missing"}
    try:
        answer = await service.search(
            "fonction publique" if provider == "legifrance" else "responsabilité",
            ["codes"] if provider == "legifrance" else ["case_law"],
            "administrative" if provider == "legifrance" else "judicial",
            date.today(),
        )
        report["checks"].append(
            {"operation": "search", "status": answer["status"], "count": len(answer["results"])}
        )
        if answer["errors"]:
            return {
                **report,
                "state": "failed",
                "error_codes": [x["code"] for x in answer["errors"]],
            }
        if not answer["results"]:
            return {**report, "state": "reachable_empty_result"}
        selected = next(
            (
                row
                for row in answer["results"]
                if row["source_ref"].startswith("legifrance:LEGIARTI")
            ),
            answer["results"][0],
        )
        fetched = await service.fetch(selected["source_ref"], date.today())
        report["checks"].append({"operation": "fetch", "status": fetched["status"]})
        if fetched["status"] != "ok":
            return {**report, "state": "failed", "error_codes": ["fetch_not_verified"]}
        return {**report, "state": "verified_search_and_fetch"}
    except SourceError as exc:
        return {**report, "state": "failed", "error_codes": [exc.problem.code]}
