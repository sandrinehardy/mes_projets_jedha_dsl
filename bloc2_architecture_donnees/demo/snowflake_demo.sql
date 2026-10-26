-- Stripe - démonstration OLAP (Snowflake). Données fictives chargées depuis S3.
-- Fichier identique à celui dans mon espace snowflake.
--


CREATE DATABASE IF NOT EXISTS stripe_demo;
CREATE SCHEMA IF NOT EXISTS stripe_demo.analytics;
USE SCHEMA stripe_demo.analytics;

CREATE OR REPLACE FILE FORMAT csv_format
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  NULL_IF = ('NULL', 'null', '');

-- Stage : le dossier S3 où sont les CSV
CREATE OR REPLACE STAGE s3_stripe_demo
  URL = 's3://NOM_DU_BUCKET/stripe-demo/olap/'
  CREDENTIALS = (AWS_KEY_ID = 'A_RENSEIGNER' AWS_SECRET_KEY = 'A_RENSEIGNER')
  FILE_FORMAT = csv_format;

LIST @s3_stripe_demo;

-- Tables du schéma en étoile
CREATE OR REPLACE TABLE dim_date (date_id INTEGER, full_date DATE, month INTEGER, year INTEGER);
CREATE OR REPLACE TABLE dim_merchant (merchant_id INTEGER, name VARCHAR, country VARCHAR);
CREATE OR REPLACE TABLE dim_customer (customer_id INTEGER, country VARCHAR);
CREATE OR REPLACE TABLE dim_payment_method (payment_method_id INTEGER, name VARCHAR);
CREATE OR REPLACE TABLE dim_country (country_id INTEGER, country_name VARCHAR, region VARCHAR);
CREATE OR REPLACE TABLE fact_transactions (
  transaction_id INTEGER, date_id INTEGER, merchant_id INTEGER, customer_id INTEGER,
  payment_method_id INTEGER, country_id INTEGER, amount NUMBER(10,2), currency CHAR(3),
  status VARCHAR, fraud_score NUMBER(3,2)
);
CREATE OR REPLACE TABLE daily_revenue (date_id INTEGER, merchant_id INTEGER, total_amount NUMBER(12,2), nb_transactions INTEGER);

-- Chargement depuis S3
COPY INTO dim_date FROM @s3_stripe_demo PATTERN = '.*dim_date.csv' FILE_FORMAT = csv_format;
COPY INTO dim_merchant FROM @s3_stripe_demo PATTERN = '.*dim_merchant.csv' FILE_FORMAT = csv_format;
COPY INTO dim_customer FROM @s3_stripe_demo PATTERN = '.*dim_customer.csv' FILE_FORMAT = csv_format;
COPY INTO dim_payment_method FROM @s3_stripe_demo PATTERN = '.*dim_payment_method.csv' FILE_FORMAT = csv_format;
COPY INTO dim_country FROM @s3_stripe_demo PATTERN = '.*dim_country.csv' FILE_FORMAT = csv_format;
COPY INTO fact_transactions FROM @s3_stripe_demo PATTERN = '.*fact_transactions.csv' FILE_FORMAT = csv_format;
COPY INTO daily_revenue FROM @s3_stripe_demo PATTERN = '.*daily_revenue.csv' FILE_FORMAT = csv_format;

-- Vérification : nombre de lignes par table
SELECT 'fact_transactions' AS table_name, COUNT(*) AS nb_lignes FROM fact_transactions
UNION ALL SELECT 'daily_revenue', COUNT(*) FROM daily_revenue
UNION ALL SELECT 'dim_merchant', COUNT(*) FROM dim_merchant
UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer;

-- Q1. Quel est le chiffre d'affaires par mois et par devise ?
SELECT d.year, d.month, f.currency, SUM(f.amount) AS revenue
FROM fact_transactions f
JOIN dim_date d ON f.date_id = d.date_id
WHERE f.status = 'successful'
GROUP BY d.year, d.month, f.currency
ORDER BY d.year, d.month;

-- Q2. Quels sont les 5 marchands qui rapportent le plus ?
SELECT m.name, SUM(r.total_amount) AS revenue
FROM daily_revenue r
JOIN dim_merchant m ON r.merchant_id = m.merchant_id
GROUP BY m.name
ORDER BY revenue DESC
LIMIT 5;

-- Q3. Combien de transactions suspectes par marchand ?
SELECT m.name, COUNT(*) AS nb_suspect
FROM fact_transactions f
JOIN dim_merchant m ON f.merchant_id = m.merchant_id
WHERE f.fraud_score >= 0.8
GROUP BY m.name
ORDER BY nb_suspect DESC;

-- Q4. Quels clients sont VIP, réguliers ou occasionnels ?
SELECT customer_id,
       SUM(amount) AS total_spent,
       CASE WHEN SUM(amount) >= 1000 THEN 'VIP'
            WHEN SUM(amount) >= 200  THEN 'régulier'
            ELSE 'occasionnel' END AS segment
FROM fact_transactions
WHERE status = 'successful'
GROUP BY customer_id;
