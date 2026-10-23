import json
from datetime import datetime

import requests
from airflow.sdk import DAG, Variable
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook

URL_API = "https://sdacelo-real-time-fraud-detection.hf.space/current-transactions"


def recuperer_transaction(ti):
    # Appel de l'API : une transaction par appel
    reponse = requests.get(URL_API, timeout=30)
    reponse.raise_for_status()
    donnees = json.loads(reponse.json())
    transaction = dict(zip(donnees["columns"], donnees["data"][0]))

    # Archivage du json dans S3
    cle = f"raw/transactions/{datetime.now():%Y/%m/%d}/{transaction['trans_num']}.json"
    S3Hook(aws_conn_id="aws_default").load_string(
        string_data=json.dumps(transaction),
        key=cle,
        bucket_name=Variable.get("bucket_name"),
        replace=True,
    )
    print("transaction stockée :", cle)

    # Transmission de la transaction à la tâche suivante
    ti.xcom_push(key="transaction", value=transaction)

def predire(ti):
    import mlflow
    import mlflow.sklearn
    import pandas as pd

    # récupération de la transaction de la tâche précédente
    transaction = ti.xcom_pull(task_ids="recuperer_transaction", key="transaction")

    # récupération du modèle
    modele = mlflow.sklearn.load_model("models:/fraud_detector@production")
    client = mlflow.MlflowClient()
    version = client.get_model_version_by_alias("fraud_detector", "production")
    seuil = float(version.tags["threshold"])

    # prediction
    ligne = pd.DataFrame([transaction])
    proba = float(modele.predict_proba(ligne)[0, 1])
    prediction = bool(proba >= seuil)
    print(f"probabilité : {proba:.4f} | seuil : {seuil} | fraude prédite : {prediction}")

    # transmision de (transaction + prediction) à la tâche suivante
    ti.xcom_push(
        key="resultat",
        value={"transaction": transaction, "proba": proba, "prediction": prediction},
    )


def ecrire_neondb(ti):
    resultat = ti.xcom_pull(task_ids="predire", key="resultat")
    t = resultat["transaction"]

    hook = PostgresHook(postgres_conn_id="fraud_db")

    # création de la table si elle n'existe pas encore
    hook.run("""
        CREATE TABLE IF NOT EXISTS transactions (
            trans_num        TEXT PRIMARY KEY,
            date_transaction TIMESTAMP,
            cc_num           BIGINT,
            merchant         TEXT,
            category         TEXT,
            amt              DOUBLE PRECISION,
            first            TEXT,
            last             TEXT,
            gender           TEXT,
            street           TEXT,
            city             TEXT,
            state            TEXT,
            zip              INTEGER,
            lat              DOUBLE PRECISION,
            long             DOUBLE PRECISION,
            city_pop         INTEGER,
            job              TEXT,
            dob              DATE,
            merch_lat        DOUBLE PRECISION,
            merch_long       DOUBLE PRECISION,
            is_fraud         INTEGER,
            proba            DOUBLE PRECISION,
            prediction   BOOLEAN
        )
    """)

    # insertion
    hook.run(
        """
        INSERT INTO transactions VALUES (
            %s, to_timestamp(%s / 1000.0), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (trans_num) DO NOTHING 
        """,
        parameters=(
            t["trans_num"], t["current_time"], t["cc_num"], t["merchant"], t["category"],
            t["amt"], t["first"], t["last"], t["gender"], t["street"], t["city"],
            t["state"], t["zip"], t["lat"], t["long"], t["city_pop"], t["job"],
            t["dob"], t["merch_lat"], t["merch_long"], t["is_fraud"],
            resultat["proba"], resultat["prediction"],
        ),
    )
    print("transaction écrite dans NeonDB :", t["trans_num"])


def alerter_discord(ti):
    resultat = ti.xcom_pull(task_ids="predire", key="resultat")
    t = resultat["transaction"]

    # pas de fraude prédite : rien à envoyer
    if not resultat["prediction"]:
        print("pas de fraude prédite, pas d'alerte :", t["trans_num"])
        return

    # message avec toutes les infos de la transaction
    lignes = [
        "**Fraude suspectée**",
        f"prediction : {resultat['prediction']}",
        f"proba : {resultat['proba']:.4f}",
    ]
    lignes += [f"{cle} : {valeur}" for cle, valeur in t.items()]
    message = "\n".join(lignes)

    reponse = requests.post(
        Variable.get("discord_webhook_url"), json={"content": message}, timeout=30
    )
    reponse.raise_for_status()
    print("alerte envoyée sur Discord :", t["trans_num"])


with DAG(
    dag_id="fraud_realtime",
    start_date=datetime(2026, 1, 1),
    schedule="* * * * *",   # toutes les minutes
    catchup=False,          # pas de rattrapage des minutes manquées
    max_active_runs=1,      # jamais deux exécutions en même temps
    tags=["fraud"],
) as dag:
    t_recuperer = PythonOperator(task_id="recuperer_transaction", python_callable=recuperer_transaction)
    t_predire = PythonOperator(task_id="predire", python_callable=predire)

    t_ecrire = PythonOperator(task_id="ecrire_neondb", python_callable=ecrire_neondb)

    t_alerter = PythonOperator(task_id="alerter_discord", python_callable=alerter_discord)

    t_recuperer >> t_predire >> [t_ecrire, t_alerter]