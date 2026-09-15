# Dossiers structurés et archive privée

Le MCP `review_case` reçoit le schéma `Dossier`. Générer sa définition exacte :

```bash
uv run droit-territorial case-schema > dossier.schema.json
```

La [méthode de dossier](../skills/juriste-territorial/references/dossier.md) explique
comment relier pièces, faits, conditions, moyens et effets. Les références de
preuve viennent d’un `fetch` réel ; un identifiant inventé reste indisponible.

## Conservation facultative

```bash
export JT_EVIDENCE_DB=/chemin/prive/preuves.sqlite
export JT_PRINCIPAL=operateur-local
export JT_LOCAL_DB=/chemin/prive/pieces.sqlite
uv run droit-territorial serve
```

Sans `JT_EVIDENCE_DB`, le cache reste limité à 32 documents/30 minutes. Avec cette
variable, les captures persistent et peuvent être relues après redémarrage.
Le principal est fourni par l’opérateur, jamais par les arguments MCP.

Une fois les preuves consultées et le dossier JSON rédigé :

```bash
uv run droit-territorial review-case dossier.json
uv run droit-territorial record-case dossier.json
uv run droit-territorial read-case record_IDENTIFIANT_RETOURNE
```

Chaque enregistrement crée une nouvelle note avec son horodatage et son contrôle.
Une note comportant des inconnues peut être conservée comme état de travail.
Elle n’est pas approuvée par son enregistrement. La relecture fournit le rapport
historique et le contrôle actuel, sans réécriture du premier. Un retrait de pièce
interdit sa restitution, y compris depuis une note historique.

`compare_evidence` compare deux captures du même document. Il distingue changement
de contenu, de métadonnées et de date d’analyse ; le signal impose un réexamen,
sans décider de l’effet juridique. Aucune collecte périodique n’est programmée.

## Frontière de confiance

SQLite reste sur le poste, fichier mode 0600 ; liens symboliques et liens physiques
du fichier d’archive sont refusés. Le répertoire parent doit être contrôlé par
l’opérateur. Les empreintes détectent une corruption, pas la falsification par
un administrateur capable de modifier simultanément texte et empreintes.
Ce n’est ni du chiffrement au repos ni une authentification multiutilisateur.

Définir localement conservation, sauvegarde et effacement. Ne jamais placer
l’archive, les réponses privées ou les pièces de travail dans le dépôt public.
