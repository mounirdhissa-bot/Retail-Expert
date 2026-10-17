# Application d'audit retail

Saisie des fiches d'audit, calcul du score et historisation dans une base SQL.
Application Streamlit, mise en ligne comme IBP Master (GitHub + Streamlit Community Cloud).

## Lancer en local

    python3 -m pip install -r requirements.txt
    streamlit run app.py

Sans configuration, la base est un fichier SQLite `audits.db` créé à côté de `app.py`.

## Mettre en ligne

1. Base de données : créer une base PostgreSQL gratuite (par exemple sur neon.tech) et copier son URL de connexion.
2. Streamlit Community Cloud (share.streamlit.io) : « Create app », choisir ce dépôt, branche `main`, fichier `app.py`.
3. Dans « Advanced settings » > « Secrets », coller :

       DATABASE_URL = "postgresql://utilisateur:motdepasse@hote/base?sslmode=require"
       APP_PASSWORD = "mot de passe d'accès à l'application"

`APP_PASSWORD` est facultatif : s'il est défini, l'application demande ce mot de passe avant tout accès
(utile si le dépôt est public). Les secrets ne sont jamais dans le dépôt.

Les tables sont créées automatiquement au premier lancement. Sans `DATABASE_URL`, l'application en ligne
utiliserait SQLite sur le serveur Streamlit, qui est effacé à chaque redémarrage : les fiches seraient perdues.

## Vérifier la connexion à Neon

La barre latérale indique la base utilisée : « PostgreSQL (hôte Neon) » avec le nombre de fiches, ou un
avertissement rouge si l'application en ligne tourne sans `DATABASE_URL`. Pour contrôler côté Neon, ouvrir
le SQL Editor et lancer `SELECT * FROM audits ORDER BY id DESC;` après avoir soumis une fiche.

## Pages

- **Accueil** : les 5 rubriques avec le nombre de fiches, le dernier audit et le score moyen.
- **Nouvelle fiche** : en-tête (magasin, auditeur, personne auditée, date), critères groupés par aspect et zone,
  évalués C / PC / NC / NA avec observations, action corrective, responsable et délai. Score en direct dans la
  barre latérale. Le bouton **Submit** enregistre la fiche.
- **Historique** : toutes les fiches, filtrables par rubrique, export CSV ; un clic ouvre la fiche
  (score par aspect, plan d'action, détail).

## Score (mêmes règles que les grilles Excel)

- C = 2 points, PC = 1, NC = 0, NA exclu, critère laissé vide = non évalué (exclu).
- Point critique : coefficient 3, autres points : coefficient 1.
- Score = points obtenus / points maximum, sur les critères évalués hors NA.
- Résultat : ≥ 85 % Satisfaisant, 70 à 85 % À améliorer, < 70 % Insuffisant. Une NC sur un point critique
  donne « Insuffisant (point critique NC) ».

Audit Caisse et Audit Responsable Magasin viennent de `sources/fiche_audit_poissonnerie_v2.xlsx`.
Zone de stockage, Cuisine et Laboratoire ont encore des critères provisoires.

## Fichiers

- `app.py` : les pages Streamlit.
- `audit_core.py` : calcul du score et accès à la base (SQLAlchemy, SQLite ou PostgreSQL).
- `rubriques.py` : les critères de chaque rubrique, les seuils et le coefficient critique.

## Base de données

- `audits` : une ligne par fiche (rubrique, magasin, auditeur, personne auditée, date, points, score, résultat,
  compteurs C/PC/NC/NA, NC critiques, commentaire).
- `audit_reponses` : une ligne par critère de chaque fiche (aspect, zone, critère, point critique, coefficient,
  évaluation, points, observations, action corrective, responsable, délai).
