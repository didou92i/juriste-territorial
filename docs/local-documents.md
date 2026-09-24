# Pièces privées locales

L’import volontaire accepte `.txt`/`.md` UTF-8, `.pdf` et `.docx`. Il conserve
**l’original**, son empreinte SHA-256, le texte extrait, son empreinte et des
repères de page, paragraphe ou ligne de tableau dans une base SQLite privée.
L’extraction PDF/DOCX est partielle : vérifier signatures, annexes, images,
notes et mise en page dans l’original avant d’en tirer une conséquence.

```bash
uv run droit-territorial import-local piece.md \
  --db private/dossiers.sqlite --principal juriste-a \
  --case dossier-001 --title "Délibération à vérifier"

# Pour un PDF scanné, après installation locale de pdftoppm et Tesseract :
uv run droit-territorial import-local scan.pdf --ocr --ocr-language fra \
  --db private/dossiers.sqlite --principal juriste-a \
  --case dossier-001 --title "Scan à relire"
```

L’OCR ne s’applique qu’aux pages PDF sans texte suffisamment extractible.
`extraction_status=ocr_unreviewed` signale une transcription à comparer au
scan. Les lignes OCR de confiance inférieure à 85/100 portent `uncertain=true` ;
une confiance élevée ne certifie pas le texte. Les résultats `fetch` exposent
les `source_locators` des passages affichés. Une délibération non importée ou
une annexe illisible demeure une pièce manquante, pas une règle présumée.

Bornes : fichier 20 Mo, texte UTF-8 2 Mo, 200 pages PDF, 2 millions de
caractères extraits, 5 000 repères. L’OCR est local ; aucun document n’est
transmis à un prestataire par l’import. La sortie du MCP, elle, est traitée
selon la configuration du modèle de votre client.

Configurer le processus MCP stdio avec `JT_LOCAL_DB` (chemin absolu) et
`JT_PRINCIPAL`. L'identité est définie par l'opérateur ; elle n'est jamais un
argument d'outil modifiable par le modèle. Un processus stdio correspond à un
utilisateur de confiance. La sécurité du compte système reste nécessaire.

La recherche filtre identité et dossier avant restitution des titres et
résultats. La consultation applique à nouveau l'identité ; les références
inconnues, retirées et non autorisées ont la même erreur. La révocation est
revérifiée avant de restituer un instantané déjà consulté.

```bash
uv run droit-territorial withdraw-local \
  --db private/dossiers.sqlite --principal juriste-a --id IDENTIFIANT
```

Cette commande retire le document des recherches et consultations ; elle
**ne supprime pas l'original de la base**. L'effacement, les sauvegardes et les
durées de conservation relèvent d'une procédure opérateur adaptée. Ne pas
confondre ce retrait avec l'exercice complet d'un droit à l'effacement.

Le HTTP local désactive les pièces privées. Un service partagé avec données
privées nécessite authentification, contrôle d'accès par dossier, séparation
des sessions et tests supplémentaires ; il n'est pas livré dans cette version.
