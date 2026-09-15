# Maintenance des sources et de la méthode

Conserver séparément version logicielle, version méthodologique, date de collecte,
date de revue et période d'application. Le registre initial est une photographie
revue le 15 septembre 2026 ; il n'est pas une veille automatique.

## Changement de texte ou règle

1. Retrouver la publication officielle et la version applicable ; identifier
   la transition, les personnes, objets et territoires concernés.
2. Comparer les textes, puis analyser la conséquence. Le diff ne tranche pas le droit.
3. Recenser les règles, modules et gabarits touchés, ainsi que les dossiers
   identifiés par l'opérateur comme dépendants.
4. Modifier le registre avec source, dates, champ, comparateur et exceptions.
5. Mettre à jour les cas de frontière et les scénarios ; faire relire les points
   juridiques sensibles par une personne compétente, puis publier une version.

Aucune mise à jour de règle n'est promue automatiquement. Les analyses historiques
conservent leurs sources et leur version ; une révision reste identifiable.

## Correction/retrait d'une source

Pour un identifiant public à neutraliser, configurer `JT_WITHDRAWN_IDS` (liste
d'identifiants séparés par virgules) puis redémarrer le processus. La liste est
appliquée à la consultation et aux preuves ; pour les pièces locales, utiliser
la commande opérateur de retrait. Ce mécanisme ne détecte pas automatiquement
toutes les demandes de correction des fournisseurs.

Rechercher les analyses dépendantes dans les dossiers conservés par l'opérateur,
actualiser leurs preuves et informer leurs responsables selon le circuit local.
Il n'existe pas de système de notification automatique dans ce pilote.

## Versions et contrôles

Les dépendances sont verrouillées dans `uv.lock`. Exécuter tests, vérification du
skill et construction de paquet avant diffusion. Mettre à jour les résultats
effectivement observés dans le rapport de validation, sans convertir un scénario
non exécuté en succès. En cas de régression, conserver la dernière version
qualifiée et suspendre explicitement la capacité concernée.

## Opérations ajoutées en 0.2.0

L’[index administratif](admin-index.md) accepte des réimports explicites et un
retrait par identifiant. L’[archive privée](case-records.md) conserve des états
anciens ; `compare_evidence` signale un réexamen. Ni cette comparaison ni les
sondes de qualification ne lancent de veille programmée.
