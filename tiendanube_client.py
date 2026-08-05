import aiohttp
from config import TIENDANUBE_USER_ID, TIENDANUBE_ACCESS_TOKEN
from sheets_writer import get_commission_rates

BASE_URL = f"https://api.tiendanube.com/v1/{TIENDANUBE_USER_ID}"
HEADERS = {
    "Authentication": f"bearer {TIENDANUBE_ACCESS_TOKEN}",
    "User-Agent": "Blooming Essie Bot (bloomingessie@gmail.com)",
    "Content-Type": "application/json",
}

# La API de Tienda Nube no informa el monto de comisión de cada orden, y la
# tasa cambia mes a mes. Por eso las tasas viven en la pestaña "⚙️ Comisiones"
# del Sheet (Juan las edita ahí, sin tocar código). Esto es solo un respaldo
# por si esa pestaña no se puede leer (ej. caída de Google Sheets) — no se
# actualiza sola, sirve para que el bot no se rompa del todo ese día.
_FALLBACK_RATES = {
    "TRF": 0.019,       # Transferencia bancaria
    "TC_1": 0.0532,     # Débito o crédito, 1 cuota
    "TC_3": 0.228569,   # Crédito, 3 cuotas
    "TC_6": 0.3072,     # Crédito, 6 cuotas
    "MP": 0.0611,       # Mercado Pago, dinero en cuenta
    "MODO_1": 0.0532,   # MODO, 1 cuota (= débito/crédito)
    "MODO_3": 0.228569, # MODO, 3 cuotas (= crédito 3 cuotas)
    "MODO_6": 0.3072,   # MODO, 6 cuotas (= crédito 6 cuotas)
    "OFFLINE": 0.0,     # "A convenir" / pago manual, sin pasarela
}


def _get_rates() -> dict:
    """Tasas vigentes: pestaña "⚙️ Comisiones" del Sheet, o el respaldo fijo
    si esa pestaña no se pudo leer."""
    try:
        rates = get_commission_rates()
    except Exception:
        rates = {}
    return rates if rates else _FALLBACK_RATES


def _card_key(prefix: str, installments: int) -> str:
    cuotas = installments if installments in (3, 6) else 1
    return f"{prefix}_{cuotas}"


def _fmt_pct(rate: float) -> str:
    s = f"{rate * 100:.4f}".rstrip("0").rstrip(".")
    return f"{s}%"


async def get_order(order_id: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/orders/{order_id}", headers=HEADERS
        ) as resp:
            resp.raise_for_status()
            return await resp.json()


async def register_webhook(event: str, url: str) -> dict:
    payload = {"event": event, "url": url}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/webhooks", headers=HEADERS, json=payload
        ) as resp:
            resp.raise_for_status()
            return await resp.json()


def calculate_commission(order: dict) -> tuple:
    """Determina medio de pago y % de comisión real de la orden, leyendo
    las tasas vigentes de la pestaña "⚙️ Comisiones" del Sheet.

    Devuelve (medio, rate, nota_extra) donde:
    - medio: "TC" | "TRF" | "MP" | "MODO" | ""
    - rate: float (0.0532 = 5.32%) o None si no se pudo determinar
      (medio o cuotas sin fila configurada en la pestaña).
    - nota_extra: detalle legible del medio (para la columna Notas).
    """
    rates = _get_rates()
    gateway = (order.get("gateway") or "").lower()
    pd = order.get("payment_details") or {}
    method = (pd.get("method") or "").lower()
    company = (pd.get("credit_card_company") or "").lower()
    installments = pd.get("installments") or 1
    cuotas = installments if installments > 1 else 1

    if method == "wire_transfer":
        rate = rates.get("TRF")
        return "TRF", rate, "Transferencia bancaria"

    if method in ("credit_card", "debit_card"):
        key = _card_key("TC", cuotas)
        rate = rates.get(key)
        if rate is not None:
            return "TC", rate, f"Débito/crédito, {cuotas} cuota(s)"
        return "TC", None, f"Crédito, {installments} cuotas (comisión no configurada)"

    if method == "wallet":
        if company == "wallet":
            rate = rates.get("MP")
            return "MP", rate, "Mercado Pago, dinero en cuenta"
        if company == "modo":
            key = _card_key("MODO", cuotas)
            rate = rates.get(key)
            if rate is not None:
                return "MODO", rate, f"MODO, {cuotas} cuota(s)"
            return "MODO", None, f"MODO, {installments} cuotas (comisión no configurada)"
        return "MP", None, f"Billetera '{company or 'desconocida'}' (comisión no configurada)"

    if method == "ticket":
        return "", None, f"Ticket/{company or 'efectivo'} (comisión no configurada)"

    if method == "custom" or gateway == "offline":
        rate = rates.get("OFFLINE", 0.0)
        return "", rate, "A convenir / pago manual"

    return "", None, f"Medio de pago desconocido (gateway={gateway or 's/d'}, method={method or 's/d'})"


def map_order_to_row(order: dict) -> list:
    """Convierte una orden de Tienda Nube al formato de fila del Sheet."""
    from datetime import datetime

    created_at = order.get("created_at", "")
    try:
        fecha = datetime.fromisoformat(created_at).strftime("%d/%m/%Y")
    except Exception:
        fecha = ""

    customer = order.get("customer") or {}
    nombre = customer.get("name") or customer.get("email") or "Sin nombre"

    n_orden = order.get("number") or order.get("id") or ""

    total = float(order.get("total") or 0)

    medio, rate, detalle = calculate_commission(order)

    if rate is not None:
        comision = round(total * rate, 2)
        total_neto = round(total - comision, 2)
        nota = f"{detalle} | Bruto: ${total:,.2f} - Comisión {_fmt_pct(rate)}: ${comision:,.2f}"
    else:
        # No sabemos la comisión real: dejamos el bruto y avisamos para
        # revisar a mano en vez de calcular mal.
        total_neto = total
        nota = f"⚠️ Revisar comisión manualmente — {detalle}. Total cargado en bruto: ${total:,.2f}"

    return [
        fecha,        # Fecha
        "Venta",      # Tipo
        "",           # Categoría
        nombre,       # Descripción (nombre cliente)
        "",           # Producto/SKU
        n_orden,      # n orden
        "",           # Precio Unit.
        total_neto,   # Total ($) -> plata real que queda
        medio,        # Medio de pago
        nota,         # Notas
    ]
