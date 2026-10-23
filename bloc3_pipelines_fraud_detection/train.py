import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import mlflow
import mlflow.sklearn

load_dotenv()

# Parametres du projet
RANDOM_STATE = 0
CSV_PATH = "fraudTest.csv"
VARIABLES_NUM = ["amt"]
VARIABLES_CAT = ["category", "state"]
VARIABLES = VARIABLES_NUM + VARIABLES_CAT

EXPERIMENT_NAME = "fraud_detection"
MODEL_NAME = "fraud_detector"

#----------------------------------------
# Chargement des donnees
df = pd.read_csv(CSV_PATH, index_col=0)
print("données chargées :", df.shape)

# features et target
X = df[VARIABLES]
y = df["is_fraud"]

# train, val, test
X_trainval, X_test, y_trainval, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)
X_train, X_val, y_train, y_val = train_test_split(
    X_trainval, y_trainval, test_size=0.25, stratify=y_trainval, random_state=RANDOM_STATE
)

for nom, partie in [("train", y_train), ("validation", y_val), ("test", y_test)]:
    print(f"{nom:<11}: {len(partie):>7} paiements, dont {partie.sum():>5} fraudes ({partie.mean()*100:.3f} %)")

#----------------------------------------
# Preprocessor et entrainement
preprocessor = ColumnTransformer(
    transformers=[
        ("categorical", OneHotEncoder(handle_unknown="ignore"), VARIABLES_CAT),
        ("numerical", StandardScaler(), VARIABLES_NUM),
    ]
)

model = Pipeline(
    steps=[
        ("preprocessing", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000)),
    ]
)

model.fit(X_train, y_train)
print("modèle entraîné")

#----------------------------------------
# Choix du seuil
proba_val = model.predict_proba(X_val)[:, 1]

seuils = np.arange(0.005, 0.201, 0.002)
lignes = []
for seuil in seuils:
    pred = (proba_val >= seuil).astype(int)
    lignes.append({
        "seuil": round(seuil, 3),
        "precision": precision_score(y_val, pred),
        "recall": recall_score(y_val, pred),
        "f1": f1_score(y_val, pred),
    })
resultats = pd.DataFrame(lignes)

meilleur = resultats["f1"].idxmax()
THRESHOLD = float(resultats.loc[meilleur, "seuil"])
print(f"seuil retenu (F1 maximal sur la validation) : {THRESHOLD}")
print(resultats.loc[meilleur].round(3))

#----------------------------------------
# Évaluation sur le test, avec le seuil retenu
proba_test = model.predict_proba(X_test)[:, 1]
pred_test = (proba_test >= THRESHOLD).astype(int)

metriques_test = {
    "test_accuracy": accuracy_score(y_test, pred_test),
    "test_precision": precision_score(y_test, pred_test),
    "test_recall": recall_score(y_test, pred_test),
    "test_f1": f1_score(y_test, pred_test),
}

for nom, valeur in metriques_test.items():
    print(f"{nom} : {valeur:.3f}")

#----------------------------------------
# Enregistrement dans MLflow
mlflow.set_experiment(EXPERIMENT_NAME)

with mlflow.start_run(run_name="logreg_amt_category_state"):
    mlflow.log_params({
        "modele": "LogisticRegression",
        "max_iter": 1000,
        "variables_num": str(VARIABLES_NUM),
        "variables_cat": str(VARIABLES_CAT),
        "seuil": THRESHOLD,
        "random_state": RANDOM_STATE,
    })
    mlflow.log_metrics(metriques_test)

    model_info = mlflow.sklearn.log_model(
        sk_model=model,
        name="model",
        input_example=X_train.head(5),
    )

print("modèle enregistré :", model_info.model_uri)

#----------------------------------------
# Registre : inscription du modèle, tag du seuil, alias "production"
client = mlflow.MlflowClient()

version = mlflow.register_model(model_uri=model_info.model_uri, name=MODEL_NAME)
client.set_model_version_tag(MODEL_NAME, version.version, "threshold", str(THRESHOLD))
client.set_registered_model_alias(MODEL_NAME, "production", version.version)

print(f"modèle {MODEL_NAME}, version {version.version} : alias 'production', seuil {THRESHOLD}")
