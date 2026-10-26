"""Charge les 4 collections du modèle NoSQL dans MongoDB (base stripe_demo), depuis S3.

Prérequis : MongoDB démarré (docker compose up -d)
Les identifiants MongoDB root / example sont ceux du docker-compose local du cours (aucun secret).
"""
import json
import os

import boto3
import pymongo
from dotenv import load_dotenv

load_dotenv()
BUCKET = os.environ["BUCKET_NAME"]
PREFIXE = "stripe-demo/nosql"
URI = "mongodb://root:example@localhost:27017/?authSource=admin"

# un index principal par collection
INDEX = {
    "logs": "timestamp",
    "user_sessions": "customer_id",
    "ml_features": "transaction_id",
    "customer_feedback": "merchant_id",
}

s3 = boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION", "eu-west-3"))
client = pymongo.MongoClient(URI)
db = client["stripe_demo"]

for nom, champ_index in INDEX.items():
    objet = s3.get_object(Bucket=BUCKET, Key="%s/%s.json" % (PREFIXE, nom))
    documents = json.loads(objet["Body"].read().decode("utf-8"))
    db[nom].drop()                    # on repart de zéro à chaque lancement
    db[nom].insert_many(documents)
    db[nom].create_index(champ_index)
    print(nom, ":", db[nom].count_documents({}), "documents chargés depuis S3, index sur", champ_index)
