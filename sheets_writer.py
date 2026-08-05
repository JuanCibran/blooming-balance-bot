import json
import gspread
from google.oauth2 import service_account

from config import GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_CREDENTIALS_JSON, SPREADSHEET_ID

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_REGISTRO = "📋 Registro Diario"
SHEET_COMISIONES = "⚙️ Comisiones"


def _get_client() -> gspread.Client:
    raw = GOOGLE_CREDENTIALS_JSON or GOOGLE_APPLICATION_CREDENTIALS
    if raw and raw.strip().startswith("{"):
        info = json.loads(raw)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_file(raw, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_sheet():
    return _get_client().open_by_key(SPREADSHEET_ID).worksheet(SHEET_REGISTRO)


def append_row(row: list):
    """Agrega una fila (lista) directamente al Registro Diario."""
    _get_sheet().append_row(row, value_input_option="USER_ENTERED")


def get_commission_rates() -> dict:
    """Lee la pestaña "⚙️ Comisiones" y devuelve {clave: tasa (0-1)}.

    La pestaña tiene columnas Clave | Descripción | % Comisión. Juan la
    edita a mano cuando Tienda Nube le cambia el porcentaje, sin tocar
    código. Si la pestaña no existe o hay un error, devuelve {} y el
    llamador decide cómo resolverlo (ver tiendanube_client._get_rates).
    """
    try:
        ws = _get_client().open_by_key(SPREADSHEET_ID).worksheet(SHEET_COMISIONES)
    except Exception:
        return {}

    rates = {}
    for row in ws.get_all_values()[1:]:
        if len(row) < 3:
            continue
        clave = (row[0] or "").strip().upper()
        pct_raw = (row[2] or "").strip()
        if not clave or not pct_raw:
            continue
        pct_raw = pct_raw.replace("%", "").strip().replace(",", ".")
        try:
            rates[clave] = float(pct_raw) / 100
        except ValueError:
            continue
    return rates


def append_movimiento(data: dict):
    """Convierte un dict del parser y lo agrega al Registro Diario."""
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
    append_row(row)
