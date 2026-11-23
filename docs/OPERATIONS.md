# Contrats SQL et exploitation

## Installation minimale

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m build
```

SQLite fonctionne sans installer les pilotes PostgreSQL/MySQL/Supabase. Installer uniquement l’extra nécessaire : `.[postgres]`, `.[mysql]`, `.[supabase]` ou `.[reports]`. Le fichier `requirements.txt` historique reste une installation complète des exemples et des notebooks.

## Requêtes et données sensibles

Les noms de tables/colonnes sont validés comme identifiants simples, puis cités par le dialecte. Seul le nom de table peut contenir `schema.table`. Les valeurs passent par des paramètres liés. Une expression SQL (tri calculé, jointure arbitraire, fragment WHERE) n’est pas acceptée comme identifiant. Ce contrôle ne remplace pas les droits du compte SQL : exposer une liste autorisée de tables à la frontière d’une API.

Les fonctions génériques ne journalisent plus le contenu d’une ligne insérée ou une valeur de filtre. Les exemples ne constituent pas une autorisation d’accès aux données de production.

## Volumes

`bulk_insert(engine, table, iterable, batch_size=1000)` consomme l’itérable par lots et conserve une transaction globale : une erreur tardive annule également les premiers lots. Les dictionnaires doivent avoir exactement les mêmes clés. La transaction peut être longue ; dimensionner le journal, les verrous et le délai d’exécution pour le volume réel.

`select_after_id(..., after_id=last_id, page_size=100)` utilise une pagination par clé. La colonne choisie doit être une clé entière unique, immuable et indexée. Les tailles de page sont limitées à 1 000. La pagination OFFSET reste disponible avec un tri explicite (par défaut `id`) ; son coût augmente avec la profondeur. `select_all` reste réservé aux petites tables car il matérialise tous les résultats.

## Atomicité métier

Un transfert vérifie le montant positif, fini et à deux décimales, puis exige l’existence du destinataire ; son absence annule le débit. Utiliser une colonne DECIMAL/NUMERIC appropriée sur PostgreSQL/MySQL pour la monnaie ; SQLite n’offre pas les garanties d’un moteur décimal bancaire.

Une commande réserve le stock par UPDATE conditionnel atomique, sans SELECT FOR UPDATE incompatible avec SQLite. Une réservation ou une insertion qui échoue annule toute la transaction. Les identifiants proviennent de RETURNING quand le dialecte le permet, sinon de lastrowid.

## Périmètre vérifié le 23 novembre 2026

37 tests passent localement avec Python 3.12, pandas et SQLAlchemy. Ils couvrent les identifiants malveillants, les valeurs paramétrées, les limites de pagination, le rollback entre lots et quatre achats concurrents pour une seule unité de stock. La wheel a été construite.

Les connexions vers des serveurs PostgreSQL/MySQL/Supabase réels n’ont pas été exécutées : configurer leurs accès, qualifier les schémas, contraintes, niveaux d’isolation, TLS et délais dans un environnement de test dédié avant une mise en production.

## Lecture SQL progressive

`iter_rows` permet de parcourir une table sans construire une liste de toutes ses
lignes dans le code appelant. `batch_size` est un entier de 1 à 1 000 et `order_by`
doit être une clé unique. Les identifiants sont validés et cités comme dans les
autres fonctions SQL.

```python
from contextlib import closing
from queries.select_queries import iter_rows

with closing(iter_rows(engine, "items", batch_size=500, order_by="id")) as rows:
    for row in rows:
        process(row)
        if should_stop():
            break
```

L'itérateur conserve une connexion jusqu'à son épuisement ou sa fermeture. Le bloc
`closing` la libère également lors d'un arrêt anticipé ou d'une exception du consommateur.
Ne pas transformer immédiatement l'itérateur en liste pour un gros volume.

SQLAlchemy reçoit `yield_per`, qui active le curseur serveur lorsque le pilote le
permet. Certains pilotes peuvent encore mettre leurs résultats en mémoire ; une
limite globale de mémoire n'est pas garantie pour chaque combinaison de pilote et
serveur. Les changements concurrents restent soumis au niveau d'isolation de la base.

Vérification locale : **43 tests** au total, dont lecture ordonnée sur plusieurs lots,
libération de connexion après exception et refus des limites ou identifiants invalides.
PostgreSQL et MySQL distants n'ont pas été contactés dans cette vérification.
