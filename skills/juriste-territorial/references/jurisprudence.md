# Lire une décision administrative pour ce dossier

Rechercher CE, CAA et TA selon la question et la période. ArianeWeb présente une
sélection utile pour la portée jurisprudentielle ; l'open data et un index local
ont une autre couverture. Le rang de juridiction ne suffit pas à déterminer
la pertinence d'une décision pour des faits, une procédure et une règle différents.

Pour chaque décision décisive, conserver :

1. Identité vérifiée, juridiction, numéro, date, texte consulté et stade procédural.
2. Faits pertinents et question effectivement tranchée.
3. Arguments des parties, motifs du juge et dispositif, clairement distingués.
4. Passage décisif et portée exacte : admission, recevabilité, urgence ou fond ;
   décision provisoire ou définitive sur le point considéré.
5. Conditions de transposition : texte applicable, faits comparables, exceptions,
   limites, éventuelle évolution ultérieure et recherche de décisions adverses.

Un rejet pour défaut d'urgence ne tranche pas nécessairement le fond. Une
non-admission ne transforme pas les moyens reproduits en règles approuvées.
Une solution isolée de première instance n'établit pas une jurisprudence constante.
Une citation présente dans la décision ne prouve pas son attribution au juge.

Avec `search_admin_archive`, essayer d'abord l'ECLI, le numéro ou l'identifiant
XML exact lorsqu'il est connu. Sinon filtrer `CE`, `CAA` ou `TA`, proposer au
plus trois `variants` de termes, puis lire les résultats classés par pertinence
lexicale. Examiner les lots et dates **réellement importés**, puis
`fetch(admin:...)` et les pages restantes. Ce classement ne mesure ni l'autorité
ni la portée de la solution. Compléter par ArianeWeb pour situer un apport
jurisprudentiel ; l'index local n'est ni national ni automatiquement à jour.

Réserver précisément le point qui dépend d'une décision introuvable ; poursuivre
l'analyse fondée sur les autres pièces. Ne pas convertir une panne, une limite
de corpus ou une recherche infructueuse en preuve d'absence de solution contraire.
