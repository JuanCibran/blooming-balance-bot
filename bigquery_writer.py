import json
import os
import uuid
from datetime import datetime, timezone

from google.cloud import bigquery
from google.oauth2 import service_account

from config import (
    BIGQUERY_PROJECT_ID,
    BIGQUERY_DATASET_ID,
    GOOGLE_APPLICATION_CREDENTIALS,
    GOOGLE_CREDENTIALS_JSON,
)

TABLE_ID = "movimientos"

SCHEMA = [
    bigquery.SchemaField("id", "STRING"),
    bigquery.SchemaField("fecha", "DATE"),
    bigquery.SchemaField("tipo", "STRING"),
    bigquery.SchemaField("categoria", "STRING"),
    bigquery.SchemaField("descripcion", "STRING"),
    bigquery.SchemaField("n_orden", "INTEGER"),
    bigquery.SchemaField("precio_unit", "FLOAT"),
    bigquery.SchemaField("total", "FLOAT"),
    bigquery.SchemaField("medio_pago", "STRING"),
    bigquery.SchemaField("notas", "STRING"),
    bigquery.SchemaField("inserted_at", "TIMESTAMP"),
]


def _get_client() -> bigquery.Client:
    if GOOGLE_CREDENTIALS_JSON:
        # Railway: credenciales como JSON string en env var
        info = json.loads(GOOGLE_CREDENTIALS_JSON)
        creds = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(project=BIGQUERY_PROJECT_ID, credentials=creds)

    if GOOGLE_APPLICATION_CREDENTIALS:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

    return bigquery.Client(project=BIGQUERY_PROJECT_ID)


def _ensure_table(client: bigquery.Client):
    full_table_id = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{TABLE_ID}"
    try:
        client.get_table(full_table_id)
    except Exception:
        table = bigquery.Table(full_table_id, schema=SCHEMA)
        client.create_table(table)


def insert_movimiento(data: dict) -> str:
    client = _get_client()
    _ensure_table(client)

    row = {
        "id": str(uuid.uuid4()),
        "fecha": data.get("fecha"),
        "tipo": data.get("tipo"),
        "categoria": data.get("categoria"),
        "descripcion": data.get("descripcion"),
        "n_orden": data.get("n_orden"),
        "precio_unit": data.get("precio_unit"),
        "total": data.get("total"),
        "medio_pago": data.get("medio_pago"),
        "notas": data.get("notas"),
        "inserted_at": datetime.now(timezone.utc).isoformat(),
    }

    full_table_id = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{TABLE_ID}"
    errors = client.insert_rows_json(full_table_id, [row])

    if errors:
        raise RuntimeError(f"Error al insertar en BigQuery: {errors}")

    return row["id"]
