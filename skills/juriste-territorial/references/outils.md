# Contrat MCP 0.1.0

Les noms ci-dessous existent dans ce serveur ; vérifier leur présence dans le
client connecté. Les préfixes du client peuvent modifier le nom affiché.

| Outil | Paramètres essentiels | Limite déterminante |
|---|---|---|
| `get_source_status` | `source_id` facultatif | Configuration et derniers appels ; pas test réseau implicite |
| `get_methodology` | `topic=core`, `output_mode=note` | Liste les sujets ; méthode expérimentale |
| `search` | `query`, `as_of_date`, `source_types`, `legal_order`, `cursor` | Date obligatoire pour codes/textes consolidés ; résultats de découverte |
| `fetch` | `source_ref`, `as_of_date`, `offset`, `length` | `evidence:` et `next_offset` pour la suite du même document |
| `get_legal_version` | `text_ref`, `article`, `as_of_date` | `text_ref` = titre exact du code ; correspondance unique requise |
| `compare_versions` | `text_ref`, `article`, `from_date`, `to_date` | Diff textuel, pas interprétation du changement |
| `search_case_law` | `query`, `legal_order`, `courts`, `date_start`, `date_end`, `cursor` | CETAT administratif ; filtre `courts` seulement pour JudiLibre |
| `resolve_references` | `source_ref`, `as_of_date`, `depth_limit` | Références explicites, profondeur 2 et 12 documents au maximum |
| `search_local_acts` | `query`, `case_id`, `as_of_date`, `offset` | Identité configurée par l'opérateur, textes importés seulement |
| `check_evidence` | `claims` | Une citation retrouvée ne prouve pas la déduction |
| `evaluate_rule` | `rule_id`, `facts`, `as_of_date` | Deux tests monétaires ; aucun délai contentieux général |

Types de recherche : `codes`, `legislation`, `jorf`, `case_law`,
`constitutional_case_law`. Ordres : `administrative`, `judicial`, `any`.
La date de consolidation ne filtre pas automatiquement les décisions ni le JORF.
Le fonds constitutionnel est disponible en découverte ; sa consultation API
spécialisée n'est pas livrée. Consulter la page officielle pour son texte.

Références de consultation : `legifrance:IDENTIFIANT`, `judilibre:IDENTIFIANT`,
`web:URL_HTTPS_OFFICIELLE`, `local:IDENTIFIANT`, `evidence:IDENTIFIANT`.
Les deux premières doivent être confirmées dans la réponse du fournisseur.
La voie web ne permet que les domaines officiels déclarés et ne garantit pas
la complétude de l'extraction HTML. Elle n'est pas un moteur de recherche web.

Après `fetch`, une preuve reçoit un identifiant émis par le serveur, l'empreinte
du texte complet récupéré, sa provenance et ses dates. La mémoire de preuves
est limitée à 32 documents et 30 minutes ; une preuve expirée doit être récupérée
de nouveau. Conserver les sorties d'outils dans le dossier de travail si nécessaire.

`check_evidence` reçoit une liste d'objets : `claim_id`, `statement`, `evidence_id`,
`quote`, `as_of_date` facultative, `fact_ids` facultatifs. Il contrôle la présence
exacte de la citation et les métadonnées de la preuve. `semantic_support` et
`legal_validity` restent `not_assessed` : le lien entre citation et conclusion
doit être établi dans l'analyse juridique.

`evaluate_rule` : `procurement.dispense` ou `procurement.formal_threshold`.
Faits nécessaires : `buyer_type=other_contracting_authority`,
`contract_type=supplies/services/works`, `amount` comme chaîne décimale,
`tax_basis=HT`, `currency=EUR`, `scope=ordinary_whole_need`,
`trigger=consultation_started/notice_sent`, `trigger_date=AAAA-MM-JJ`.
`as_of_date` doit correspondre à ce fait générateur. Le résultat ne choisit pas
la procédure et ne dispense pas des autres conditions ni d'une revalidation.

Pas d'index XML administratif, de moteur vectoriel, d'OCR ni de service HTTP
partagé dans cette version. Pour ArianeWeb/open data, utiliser la recherche web
du client et consulter les pages officielles. Le HTTP fourni se limite à la
boucle locale, sans accès aux pièces privées. Une intégration distante exige
un déploiement et une authentification propres, non inclus ici.
