FROM python:3.12-slim

WORKDIR /home/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

CMD ["bash", "-c", "mlflow server --host 0.0.0.0 --port 7860 --backend-store-uri \"$BACKEND_STORE_URI\" --artifacts-destination \"$ARTIFACT_STORE_URI\" --serve-artifacts --allowed-hosts '*' --cors-allowed-origins '*'"]
