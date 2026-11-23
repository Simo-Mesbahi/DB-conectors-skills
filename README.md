# DB-connectors-skills

Ressource pédagogique complète et professionnelle pour maîtriser le cycle
complet **connexion → requêtage → exploitation** de bases de données avec
Python, en couvrant **Supabase, PostgreSQL, MySQL et SQLite**.

Ce repo n'est pas juste "comment se connecter" : il va jusqu'à **l'exploitation
concrète du résultat des requêtes** (nettoyage, analyse, visualisation, export,
action métier automatique).

---

## 🗺️ Vue d'ensemble du pipeline

```
 CONNEXION          REQUÊTAGE              EXPLOITATION DU RÉSULTAT
┌──────────┐      ┌─────────────┐      ┌──────────────────────────────┐
│ Supabase │      │ SELECT      │      │ DataFrame → Nettoyage        │
│ Postgres │ ───► │ INSERT      │ ───► │ → Analyse (stats, agrégats)  │
│ MySQL    │      │ UPDATE      │      │ → Visualisation (graphiques) │
│ SQLite   │      │ DELETE      │      │ → Export (CSV/Excel/JSON/DB) │
└──────────┘      │ Transactions│      │ → Action métier (alerte...)  │
                   └─────────────┘      └──────────────────────────────┘
```

## 📁 Structure du repo

```
DB-connectors-skills/
├── db_connection/          # Connexion aux bases (le "comment se connecter")
│   ├── supabase_connector.py     # SDK Supabase + connexion SQL directe
│   ├── postgresql_connector.py   # psycopg2 + SQLAlchemy, retry auto
│   ├── mysql_connector.py        # mysql-connector + SQLAlchemy, retry auto
│   ├── sqlite_connector.py       # sqlite3 + SQLAlchemy
│   └── connection_utils.py       # Factory unique get_engine("postgresql"|...)
│
├── queries/                 # Requêtage (le "comment interroger")
│   ├── select_queries.py         # SELECT simples, filtrés, jointures, pagination
│   ├── write_queries.py          # INSERT, UPDATE, DELETE, bulk_insert, upsert
│   └── transactions.py           # Transactions "tout ou rien"
│
├── data_processing/         # Exploitation (le "comment utiliser le résultat")
│   ├── result_to_dataframe.py    # Résultat brut → pandas.DataFrame
│   ├── clean_transform.py        # Nettoyage, typage, filtres, colonnes calculées
│   ├── analyze_results.py        # Statistiques, agrégations, top N, anomalies
│   ├── visualize_results.py      # Graphiques matplotlib / plotly
│   └── export_results.py         # Export CSV / Excel / JSON / réinjection SQL
│
├── examples/                 # Cas d'usage complets de bout en bout
│   ├── exemple_1_rapport_ventes_supabase.py
│   ├── exemple_2_sync_mysql_vers_postgres.py
│   └── exemple_3_alerte_anomalie_stock.py
│
├── notebooks/                 # Version pédagogique interactive (Jupyter)
│   ├── 01_installation_setup.ipynb
│   ├── 02_connexion_bases_donnees.ipynb
│   ├── 03_requetage.ipynb
│   ├── 04_exploitation_resultats.ipynb   ← notebook central
│   ├── 05_supabase_specifique.ipynb
│   └── 06_projet_complet_pipeline.ipynb
│
├── utils/                     # Utilitaires transverses
│   ├── env_loader.py              # Chargement sécurisé du .env
│   └── logger.py                  # Logging uniforme
│
├── tests/                     # Tests unitaires (pytest)
│   ├── test_data_processing.py
│   └── test_sqlite_connector.py
│
├── .env.example                # Modèle de configuration (à copier en .env)
├── .gitignore
└── requirements.txt
```

## 🚀 Démarrage rapide

```bash
# 1. Cloner le repo
git clone https://github.com/Simo-Mesbahi/DB-conectors-skills.git
cd DB-conectors-skills

# 2. Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les accès aux bases de données
cp .env.example .env
# → éditer .env avec tes vraies valeurs (Supabase, PostgreSQL, MySQL, SQLite)

# 5. Lancer les notebooks
jupyter notebook notebooks/

# --- OU lancer directement un exemple complet ---
python -m examples.exemple_1_rapport_ventes_supabase
```

## 📚 Par où commencer ?

| Tu veux... | Va voir... |
|---|---|
| Comprendre toute la logique pas à pas | `notebooks/01` → `notebooks/06`, dans l'ordre |
| Juste te connecter à Supabase | `db_connection/supabase_connector.py` |
| Un exemple de requête paramétrée sécurisée | `queries/select_queries.py` / `write_queries.py` |
| Transformer un résultat SQL en graphique | `data_processing/visualize_results.py` |
| Un exemple **complet** copiable-collable | dossier `examples/` |
| Le notebook le plus important (exploitation) | `notebooks/04_exploitation_resultats.ipynb` |

## 🔒 Sécurité — à retenir

- **Jamais** de clé/mot de passe en dur dans le code : tout passe par `.env` (voir `utils/env_loader.py`).
- **Toutes** les requêtes du repo sont **paramétrées** (`:param` avec SQLAlchemy) → protection anti-injection SQL.
- Le fichier `.env` est dans `.gitignore` : il ne sera jamais poussé sur GitHub.
- Pour Supabase, préfère la clé `anon` (respecte RLS) à la clé `service_role` sauf besoin backend explicite.

## 🧪 Tests

```bash
pytest tests/
```

Les tests sur `data_processing/` sont 100% indépendants d'une vraie base
(ils travaillent sur des DataFrames en mémoire). Les tests sur SQLite créent
une base temporaire automatiquement. Les connecteurs Supabase/PostgreSQL/MySQL
nécessitent des identifiants valides dans `.env` pour être testés en conditions réelles.

## 🧩 Bases de données couvertes

| Base | Connexion SDK | Connexion SQL directe | Retry auto |
|---|:---:|:---:|:---:|
| **Supabase** | ✅ (`supabase-py`) | ✅ (SQLAlchemy) | — |
| **PostgreSQL** | — | ✅ (psycopg2 + SQLAlchemy) | ✅ |
| **MySQL** | — | ✅ (mysql-connector + SQLAlchemy) | ✅ |
| **SQLite** | — | ✅ (sqlite3 + SQLAlchemy) | — (pas nécessaire, fichier local) |

## 🤝 Contribuer

Les contributions sont bienvenues : nouveaux connecteurs (MongoDB, Firebase...),
nouveaux exemples de pipelines, amélioration des notebooks. Ouvre une issue ou
une pull request.

---

*Ce repo a vocation pédagogique : il montre les bonnes pratiques (sécurité,
gestion d'erreurs, structuration du code) autant que la technique elle-même.*


## Version 1.1 — contrats sûrs et traitements bornés

Installation légère : `python -m pip install -e '.[dev]'`, puis `python -m pytest -q`. Les pilotes distants sont optionnels et chargés uniquement lorsqu’ils sont demandés.

Identifiants SQL validés/cités, pagination par clé, insertion itérable par lots, contrôle des montants et transactions de stock atomiques. [Guide d’exploitation et périmètre de vérification](docs/OPERATIONS.md).
