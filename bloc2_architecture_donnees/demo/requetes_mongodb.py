"""Lance les 3 requêtes MongoDB du projet Stripe"""
import pprint

import pymongo

client = pymongo.MongoClient("mongodb://root:example@localhost:27017/?authSource=admin")
db = client["stripe_demo"]

print("\n--- M1. Les 10 transactions les plus suspectes")
resultat = db["ml_features"].find(
    {"fraud_score": {"$gte": 0.8}},
    {"_id": 0, "transaction_id": 1, "fraud_score": 1},
).sort("fraud_score", -1).limit(10)
for doc in resultat:
    pprint.pprint(doc)

print("\n--- M2. Note moyenne de chaque marchand")
pipeline = [
    {"$group": {"_id": "$merchant_id", "avg_rating": {"$avg": "$rating"}}},
    {"$sort": {"avg_rating": -1}},
]
for doc in db["customer_feedback"].aggregate(pipeline):
    pprint.pprint(doc)

print("\n--- M3. Nombre de sessions par type d'appareil")
pipeline = [{"$group": {"_id": "$device_type", "nb_sessions": {"$sum": 1}}}]
for doc in db["user_sessions"].aggregate(pipeline):
    pprint.pprint(doc)
