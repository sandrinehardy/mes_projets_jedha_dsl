# Bloc 3 – Automatic Fraud Detection : pipeline de détection de fraude

Lien GitHub du projet : https://github.com/sandrinehardy/mes_projets_jedha_dsl/tree/main/bloc3_pipelines_fraud_detection

Projet du bloc 3 (pipelines de données, option Lead : orchestration de workflows). Un modèle de détection de fraude par carte bancaire est intégré dans un pipeline automatisé, hébergé dans le cloud, qui répond à trois besoins métier :

- une **alerte Discord** dès qu'une transaction est prédite comme frauduleuse
- un **rapport quotidien** envoyé chaque matin, avec les paiements et les fraudes de la veille
- une **API temps réel** interrogée toutes les minutes (une transaction par appel)

## Liens utiles

| Élément | Rôle | Accès |
| --- | --- | --- |
| Vidéo de démonstration (environ 3 min) | Le pipeline en fonctionnement | https://drive.google.com/file/d/1Tm991lNwCVclgYKwdnYMkrh8LKzrrVo9/view?usp=sharing |
| Captures d'écran | Un écran par outil présenté | [`captures_bloc3_infrastructure.pdf`](captures_bloc3_infrastructure.pdf) |
| Schéma d'infrastructure | Trajet d'un paiement et détail des deux DAGs | [`schema_infrastructure_bloc3.pptx`](schema_infrastructure_bloc3.pptx) |
| Airflow (AWS EC2) | Orchestration des deux DAGs | http://13.36.165.234 (accès limité à mon adresse IP, machine arrêtée après l'examen) |
| Serveur MLflow (Hugging Face) | Suivi des expériences et registre de modèles | https://huggingface.co/spaces/Sandrine-dsfs36/mlflow-server-lead (espace privé) |
| Code | Dépôt GitHub (ce dossier) | https://github.com/sandrinehardy/mes_projets_jedha_dsl |

Les autres services (NeonDB, S3, Discord) n'ont pas de lien public : ils sont montrés dans la vidéo et dans les captures.

## Architecture

| Brique | Rôle | Hébergement |
| --- | --- | --- |
| API de transactions | Source des paiements, une transaction par appel | Jedha |
| Airflow 3.3.2 (Docker Compose) | Orchestre les deux DAGs, calcule la prédiction | AWS EC2 (t3.medium) |
| MLflow 3.17.2 | Registre de modèles (alias `production`, tag `threshold`) | Hugging Face (Space Docker) |
| NeonDB (PostgreSQL) | `fraud_db` : table `transactions` ; `mlflow_db` : registre MLflow | Neon |
| Amazon S3 | `raw/` : JSON bruts de l'API ; `mlflow-artifacts/` : fichiers du modèle | AWS |
| Discord | Alertes de fraude et rapport quotidien | Discord (webhook) |

### Le trajet d'un paiement

1. **Paiement** : l'API de transactions publie un paiement par appel, mis à jour chaque minute.
2. **Récupérer** : le DAG `fraud_realtime` appelle l'API chaque minute et archive le JSON brut dans S3.
3. **Prédire** : la tâche `predire` charge le modèle et le seuil depuis MLflow et calcule la probabilité de fraude.
4. **Stocker** : la transaction, la probabilité et la prédiction sont écrites dans NeonDB (sans doublon, grâce à la clé primaire `trans_num`).
5. **Alerter** : si une fraude est prédite, un message part sur Discord (en parallèle de l'étape 4).
6. **Rapport** : chaque matin à 8h (heure de Paris), le DAG `fraud_daily_report` lit les paiements de la veille dans NeonDB, calcule les statistiques et envoie le rapport sur Discord.

### Les deux DAGs

| DAG | Planification | Tâches |
| --- | --- | --- |
| `fraud_realtime` | toutes les minutes | `recuperer_transaction` → `predire` → `ecrire_neondb` et `alerter_discord` (en parallèle) |
| `fraud_daily_report` | tous les jours à 8h (Paris) | `lire_paiements` → `calculer_statistiques` → `envoyer_rapport` |

Les tâches s'échangent de petits objets par XCom (la transaction, le résultat de la prédiction, le dictionnaire de statistiques).

## Contenu du dossier

- `train.py` : entraînement du modèle et enregistrement dans MLflow (alias `production`, tag `threshold`)
- `01_eda_modele_fraude.ipynb` : exploration des données et choix du modèle
- `mlflow_server/` : `Dockerfile` du serveur MLflow déployé sur Hugging Face
- `airflow/` : `Dockerfile`, `docker-compose.yaml`, `requirements.txt`, `.env.example` et `dags/` (les deux DAGs et un DAG de test des connexions)
- `captures_bloc3_infrastructure.pdf` : captures d'écran de l'infrastructure en fonctionnement
- `schema_infrastructure_bloc3.pptx` : schéma d'infrastructure

## Variables d'environnement

Elles se trouvent dans un fichier `airflow/.env`, jamais publié (voir `.env.example`). Noms des variables :

| Variable | Rôle |
| --- | --- |
| `AIRFLOW_UID`, `FERNET_KEY`, `AIRFLOW__API_AUTH__JWT_SECRET` | configuration d'Airflow |
| `_AIRFLOW_WWW_USER_USERNAME`, `_AIRFLOW_WWW_USER_PASSWORD` | compte administrateur d'Airflow |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, `BUCKET_NAME` | accès au bucket S3 |
| `FRAUD_DB_URI` | adresse de la base `fraud_db` (NeonDB) |
| `DISCORD_WEBHOOK_URL` | webhook du salon Discord |
| `MLFLOW_TRACKING_URI`, `MLFLOW_TRACKING_TOKEN` | serveur MLflow et son jeton d'accès |

## Lancer le projet

Entraîner et enregistrer le modèle (nécessite `fraudTest.csv` à côté de `train.py` et un fichier `.env` avec les variables MLflow) :

```bash
python train.py
```

Lancer Airflow avec Docker (local ou serveur) :

```bash
cd airflow
cp .env.example .env   # puis compléter toutes les variables
docker compose build
docker compose up -d
docker compose ps
```

L'interface est alors disponible sur http://localhost:8080. Sur l'EC2, le port 8080 du conteneur est publié sur le port 80 de la machine. Les connexions Airflow (base, AWS) et les variables (bucket, webhook) sont définies par variables d'environnement.

## Résultats

- Pipeline temps réel : une exécution par minute, incluant la détection de fraude.
- Exemple de rapport quotidien (24/10/2026) : 1 437 paiements, 7 fraudes réelles, 11 fraudes prédites, 5 fraudes bien détectées.

## Limites et pistes d'amélioration

- Améliorer le modèle qui prédit aujourd'hui trop de faux positifs. Pour cela, il faudrait estimer le coût d'un faux positif.
- Le rapport est calculé en Python à partir de lignes transmises par XCom, c'est possible car on utilise peu de données. Avec davantage de données, on calculerait directement en SQL dans la base (ELT) ou on passerait par S3.
- Le modèle est chargé depuis MLFlow (HuggingFace) à chaque prédiction. On pourrait créer une API dédiée qui le garderait en mémoire pour accélérer les temps de calcul.
- Sécurité : les notifications sur discord contiennent toutes les informations de la transaction. S'il s'agissait de données réelles, on ne les exposerait pas.


