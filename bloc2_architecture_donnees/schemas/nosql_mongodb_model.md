# Stripe - Modèle NoSQL (MongoDB)

Les identifiants (transaction_id, customer_id, merchant_id) sont les mêmes que dans la base OLTP.


## 1. logs
```json
{ "timestamp": "2026-10-25T10:32:11Z", "level": "ERROR",
  "message": "Card declined", "transaction_id": 1052 }
```
Index : timestamp.

## 2. user_sessions
```json
{ "customer_id": 87, "device_type": "mobile",
  "events": [ { "type": "page_view", "page": "/checkout" },
              { "type": "click", "element": "pay_button" } ] }
```
`events` imbriqué (lu avec la session). `customer_id` référencé.
Index : customer_id.

## 3. ml_features
```json
{ "transaction_id": 1052,
  "features": { "amount": 129.9, "nb_txn_last_hour": 4, "new_device": true },
  "fraud_score": 0.87 }
```
`features` imbriqué (le modèle le lit d'un bloc). `transaction_id` référencé.
Index : transaction_id.

## 4. customer_feedback
```json
{ "customer_id": 87, "merchant_id": 12, "rating": 4,
  "comment": "Paiement rapide" }
```
`customer_id` et `merchant_id` référencés (leurs infos sont dans l'OLTP).
Index : merchant_id.
