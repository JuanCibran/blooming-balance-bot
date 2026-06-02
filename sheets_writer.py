import json
import gspread
from google.oauth2 import service_account

from config import GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_CREDENTIALS_JSON, SPREADSHEET_ID

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_REGISTRO = "📋 Registro Diario"


def _get_client() -> gspread.Client:
    if GOOGLE_CREDENTIALS_JSON:
        info = json.loads(GOOGLE_CREDENTIALS_JSON)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES
        )
    return gspread.authorize(creds)


def append_movimiento(data: dict):
    """Agrega una fila al Registro Diario del Sheet."""
    client = _get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_REGISTRO)

    # Orden de columnas: Fecha | Tipo | Categoría | Descripción | Producto/SKU |
    #                    n orden | Precio Unit. | Total ($) | Medio de pago | Notas
    row = [
        data.get("fecha", ""),
        (data.get("tipo") or "").capitalize(),
        data.get("categoria") or "",
        data.get("descripcion") or "",
        data.get("producto_sku") or "",
        data.get("n_orden") or "",
        data.get("precio_unit") or "",
        data.get("total") or "",
        (data.get("medio_pago") or "").upper(),
        data.get("notas") or "",
    ]

    sheet.append_row(row, value_input_option="USER_ENTERED")
