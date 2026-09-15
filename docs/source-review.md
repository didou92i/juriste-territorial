# Revue finale des sources de conception

Vérification des dépôts effectuée le 15 septembre 2026 via GitHub. Les têtes de
`main` correspondent toujours aux trois commits du plan fourni. Les fichiers
consultés et leurs empreintes sont consignés dans `THIRD_PARTY.yml`.

| Source | Décision de construction |
|---|---|
| Brisson 3.5.0 | Adapter les principes de méthode avec attribution CC BY-SA ; réécrire le noyau territorial. Réimplémenter les opérations du MCP dans un logiciel distinct. |
| Tanguy | Conserver la séparation recherche/consultation et les fonds utiles comme références techniques. Contrôler les contrats contre la documentation officielle. |
| Gruuuprimes | Reprendre les besoins métier comme pistes ; réécrire les modules. Exclure les noyaux anciens, scores d'autorité, corpus et copies dont les droits ne sont pas établis. |

## Précisions apportées au plan

1. **Consultation administrative chez Tanguy.** Le `consult()` examiné dirige
   `JURITEXT` vers `/consult/juri`, mais ne prévoit pas de branche `CETATEXT` ;
   ces identifiants tombent dans le repli JORF. Le nouveau connecteur distingue
   ces préfixes ; un test vérifie la route. C'est un constat de code, pas une
   affirmation de panne mesurée sur son serveur.
2. **Identité de la preuve.** Le nouveau normaliseur exige que l'identifiant
   soit confirmé dans la réponse API ; il ne complète pas une réponse sans
   identifiant par celui de la demande.
3. **Contrat récent MCP.** Le SDK officiel actuellement installé est `mcp 2.2.0`.
   Ses structures Python emploient notamment `structured_content` et `is_error`.
   Les échanges réels sont testés avec ce SDK ; aucune compatibilité client non
   observée n'est présentée comme acquise.
4. **Open data administratif.** La recherche web et les lots XML/ZIP sont
   documentés ; un index et son entretien sont un chantier distinct. Aucun
   endpoint REST hypothétique n'a été implémenté.
5. **Publication.** Un dépôt et une version pilote peuvent être publics avec
   leurs limites. Une validation juridique indépendante et les recettes API
   authentifiées demeurent nécessaires pour une qualification opérationnelle.

## Sources primaires techniques

- [FAQ API Légifrance](https://www.legifrance.gouv.fr/contenu/pied-de-page/foire-aux-questions-api) :
  OAuth, recherche datée, consultation d'articles, fonds CETAT.
- [OpenAPI officiel JudiLibre](https://github.com/Cour-de-cassation/judilibre-search/blob/dev/public/JUDILIBRE-public.json) :
  `/search`, `/decision`, `/taxonomy`, tableaux répétés et pagination.
- [Données ouvertes de la justice administrative](https://opendata.justice-administrative.fr/index.html) :
  couverture, recherche et fichiers XML/ZIP.
- [SDK MCP officiel](https://github.com/modelcontextprotocol/python-sdk) : transports et schémas.

Les exemples de contrats ne prouvent pas que tous les endpoints fonctionnent
avec une application PISTE donnée. Cette distinction figure dans le rapport de validation.
