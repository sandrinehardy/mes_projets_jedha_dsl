from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from airflow.sdk import DAG, Variable
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Paiements de la veille (jour de Paris). Les dates sont stockées en UTC dans la base :
# on les convertit en heure de Paris avant de comparer les jours.
REQUETE_VEILLE = """
    SELECT trans_num, date_transaction, amt, category, is_fraud, proba, prediction
    FROM transactions
    WHERE (date_transaction AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Paris')::date
          = (now() AT TIME ZONE 'Europe/Paris')::date - 1
"""


def lire_paiements(ti):
    import pandas as pd

    # lecture des paiements de la veille dans NeonDB
    hook = PostgresHook(postgres_conn_id="fraud_db")
    lignes = hook.get_records(REQUETE_VEILLE)
    colonnes = ["trans_num", "date_transaction", "amt", "category",
                "is_fraud", "proba", "prediction"]
    df = pd.DataFrame(lignes, columns=colonnes)
    veille = datetime.now(ZoneInfo("Europe/Paris")).date() - timedelta(days=1)
    libelle = "du " + veille.strftime("%d/%m/%Y")

    print(f"{len(df)} paiements lus ({libelle})")

    # on ne garde que ce qui sert aux statistiques
    paiements = df[["amt", "is_fraud", "prediction"]].to_dict("records")
    ti.xcom_push(key="paiements", value={"libelle": libelle, "paiements": paiements})


def calculer_statistiques(ti):
    import pandas as pd

    lecture = ti.xcom_pull(task_ids="lire_paiements", key="paiements")
    df = pd.DataFrame(lecture["paiements"], columns=["amt", "is_fraud", "prediction"])

    stats = {
        "libelle": lecture["libelle"],
        "nb_paiements": len(df),
        "montant_total": float(df["amt"].sum()),
        "nb_fraudes_reelles": int(df["is_fraud"].sum()),
        "montant_fraudes": float(df[df["is_fraud"] == 1]["amt"].sum()),
        "nb_fraudes_predites": int(df["prediction"].sum()),
        "nb_fraudes_detectees": int(((df["is_fraud"] == 1) & df["prediction"]).sum()),
    }
    print(stats)
    ti.xcom_push(key="stats", value=stats)


def envoyer_rapport(ti):
    s = ti.xcom_pull(task_ids="calculer_statistiques", key="stats")

    message = "\n".join([
        f"**Rapport {s['libelle']}**",
        f"paiements : {s['nb_paiements']}",
        f"montant total : {s['montant_total']:.2f} $",
        f"fraudes réelles : {s['nb_fraudes_reelles']} (montant : {s['montant_fraudes']:.2f} $)",
        f"fraudes prédites par le modèle : {s['nb_fraudes_predites']}",
        f"fraudes réelles bien détectées : {s['nb_fraudes_detectees']}",
    ])

    reponse = requests.post(
        Variable.get("discord_webhook_url"), json={"content": message}, timeout=30
    )
    reponse.raise_for_status()
    print("rapport envoyé sur Discord")


with DAG(
    dag_id="fraud_daily_report",
    start_date=datetime(2026, 1, 1),
    schedule="0 8 * * *",   # tous les jours à 8h (heure de Paris)
    catchup=False,
    tags=["fraud"],
) as dag:
    t_lire = PythonOperator(task_id="lire_paiements", python_callable=lire_paiements)
    t_calculer = PythonOperator(task_id="calculer_statistiques", python_callable=calculer_statistiques)
    t_envoyer = PythonOperator(task_id="envoyer_rapport", python_callable=envoyer_rapport)

    t_lire >> t_calculer >> t_envoyer
