# Stripe - Requêtes SQL (OLAP) et NoSQL (MongoDB)

## Requêtes SQL (base OLAP)

### Q1. Quel est le chiffre d'affaires par mois et par devise ?
```sql
SELECT d.year, d.month, f.currency, SUM(f.amount) AS revenue
FROM fact_transactions f
JOIN dim_date d ON f.date_id = d.date_id
WHERE f.status = 'successful'
GROUP BY d.year, d.month, f.currency
ORDER BY d.year, d.month;
```
Résultat attendu : une ligne par mois et par devise avec le total.

### Q2. Quels sont les 5 marchands qui rapportent le plus ?
```sql
SELECT m.name, SUM(r.total_amount) AS revenue
FROM daily_revenue r
JOIN dim_merchant m ON r.merchant_id = m.merchant_id
GROUP BY m.name
ORDER BY revenue DESC
LIMIT 5;
```
Résultat attendu : 5 lignes. On lit la table de résultats déjà calculés.

### Q3. Combien de transactions suspectes par marchand ?
```sql
SELECT m.name, COUNT(*) AS nb_suspect
FROM fact_transactions f
JOIN dim_merchant m ON f.merchant_id = m.merchant_id
WHERE f.fraud_score >= 0.8
GROUP BY m.name
ORDER BY nb_suspect DESC;
```
Résultat attendu : les marchands classés par nombre de paiements à score de fraude >= 0.8.

### Q4. Quels clients sont VIP, réguliers ou occasionnels ?
```sql
SELECT customer_id,
       SUM(amount) AS total_spent,
       CASE WHEN SUM(amount) >= 1000 THEN 'VIP'
            WHEN SUM(amount) >= 200  THEN 'régulier'
            ELSE 'occasionnel' END AS segment
FROM fact_transactions
WHERE status = 'successful'
GROUP BY customer_id;
```
Résultat attendu : un client par ligne avec son total dépensé et son segment.

## Requêtes NoSQL (MongoDB)

### M1. Quelles sont les 10 transactions les plus suspectes ?
```javascript
db.ml_features.find(
  { fraud_score: { $gte: 0.8 } },
  { _id: 0, transaction_id: 1, fraud_score: 1 }
).sort({ fraud_score: -1 }).limit(10)
```

### M2. Quelle est la note moyenne de chaque marchand ?
```javascript
db.customer_feedback.aggregate([
  { $group: { _id: "$merchant_id", avg_rating: { $avg: "$rating" } } },
  { $sort: { avg_rating: -1 } }
])
```

### M3. Combien de sessions par type d'appareil ?
```javascript
db.user_sessions.aggregate([
  { $group: { _id: "$device_type", nb_sessions: { $sum: 1 } } }
])
```
