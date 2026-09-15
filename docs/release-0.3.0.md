# Vos sources juridiques, simplement connectées

Juriste territorial accompagne désormais l'activation des sources dès le premier
échange. Chacun utilise ses propres accès : le dépôt ne distribue aucune clé.

## Ce qui change

- `get_source_status` présente les accès manquants et le parcours d'installation.
- Le skill et les instructions MCP demandent un rappel bref, sans solliciter de secret dans le chat.
- `configure piste` enregistre un couple OAuth avec saisie masquée dans le trousseau
  système ; profils production et sandbox séparés, aucun repli en clair.
- Les processus hébergés utilisent les variables de leur gestionnaire de secrets.
- `doctor --probe` et `get_source_status(probe=true)` distinguent recherche et
  lecture réussies, refus d'accès, panne, quota et réponse sans résultat.
- JudiLibre reste facultatif ; l'index administratif CE/CAA/TA ne demande pas de clé.

## Validation et limites

145 tests réussis, 1 test en ligne ignoré par défaut. Les 23 nouveaux cas couvrent
notamment la confidentialité des sorties, les profils incomplets, les interruptions
de saisie, le trousseau verrouillé et les différents résultats du diagnostic.
Les contrôles de style, liens du skill et déclaration des 14 outils passent.

Les tests des API utilisent des réponses simulées. La validation d'une connexion
personnelle se fait après saisie des accès avec le diagnostic explicite. Elle ne
vaut ni qualification historique complète ni validation juridique humaine.
Le HTTP fourni reste local ; aucun service distant public authentifié n'est livré.

[Activer les sources](../skills/juriste-territorial/references/installation.md)
· [Installation du MCP](compatibility.md)
