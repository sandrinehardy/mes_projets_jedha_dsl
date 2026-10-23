from datetime import datetime

import requests
from airflow.sdk import DAG, Variable
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook


def lire_variable():
    bucket = Variable.get("bucket_name")
    print("bucket :", bucket)


def tester_s3():
    bucket = Variable.get("bucket_name")
    cles = S3Hook(aws_conn_id="aws_default").list_keys(bucket_name=bucket, prefix="mlflow-artifacts/")
    print("fichiers dans mlflow-artifacts/ :", len(cles or []))


def tester_neondb():
    resultat = PostgresHook(postgres_conn_id="fraud_db").get_first("SELECT 1")
    print("réponse de NeonDB :", resultat)


def tester_discord():
    url = Variable.get("discord_webhook_url")
    reponse = requests.post(url, json={"content": "Test Airflow : la notification fonctionne."})
    print("code Discord :", reponse.status_code)
    reponse.raise_for_status()


with DAG(
    dag_id="test_connexions",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test"],
) as dag:
    t_variable = PythonOperator(task_id="lire_variable", python_callable=lire_variable)
    t_s3 = PythonOperator(task_id="tester_s3", python_callable=tester_s3)
    t_db = PythonOperator(task_id="tester_neondb", python_callable=tester_neondb)
    t_discord = PythonOperator(task_id="tester_discord", python_callable=tester_discord)

    t_variable >> [t_s3, t_db, t_discord]