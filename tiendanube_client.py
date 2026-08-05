import aiohttp
from config import TIENDANUBE_USER_ID, TIENDANUBE_ACCESS_TOKEN

BASE_URL = f"https://api.tiendanube.com/v1/{TIENDANUBE_USER_ID}"
HEADERS = {
    "Authentication": f"bearer {TIENDANUBE_ACCESS_TOKEN}",
    "User-Agent": "Blooming Essie Bot (bloomingessie@gmail.com)",
    "Content-Type": "application/json",
}

# Comisiones reales según medio de pago / cuotas (Pago Nube y Mercado Pago).
# Confirmadas por Juan el 04/08/2026. Si Tienda Nube cambia sus tasas, hay
# que actualizar esto a mano (la API no informa el monto de comisión).
COMMISSION_TRANSFER = 0.019         # Transferencia bancaria
COMMISSION_CARD_1_CUOTA = 0.0532    # Débito o crédito, 1 cuota
COMMISSION_CARD_3_CUOTAS = 0.228569 # Crédito, 3 cuotas
COMMISSION_CARD_6_CUOTAS = 0.3072   # Crédito, 6 cuotas
COMMISSION_MP_WALLET = 0.0611       # Mercado Pago, dinero en cuenta
COMMISSION_OFFLINE = 0.0            # "A convenir" / pago manual, sin pasarela
# MODO cobra la misma comisión que tarjeta débito/crédito según cuotas.
CARD_RATES_BY_INSTALLMENTS = {
    1: (COMMISSION_CARD_1_CUOTA, "1 cuota"),
    3: (COMMISSION_CARD_3_CUOTAS, "3 cuotas"),
    6: (COMMISSION_CARD_6_CUOTAS, "6 cuotas"),
}


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
    """Determina medio de pago y % de comisión real de la orden.

    Devuelve (medio, rate, nota_extra) donde:
    - medio: "TC" | "TRF" | "MP" | ""
    - rate: float (0.0532 = 5.32%) o None si no se pudo determinar
      (medio no configurado todavía, ej. MODO o Pago Fácil).
    - nota_extra: detalle legible del medio (para la columna Notas).
    """
    gateway = (order.get("gateway") or "").lower()
    pd = order.get("payment_details") or {}
    method = (pd.get("method") or "").lower()
    company = (pd.get("credit_card_company") or "").lower()
    installments = pd.get("installments") or 1

    if method == "wire_transfer":
        return "TRF", COMMISSION_TRANSFER, "Transferencia bancaria"

    if method in ("credit_card", "debit_card"):
        rate_info = CARD_RATES_BY_INSTALLMENTS.get(installments if installments > 1 else 1)
        if rate_info:
            rate, label = rate_info
            return "TC", rate, f"Débito/crédito, {label}"
        return "TC", None, f"Crédito, {installments} cuotas (comisión no configurada)"

    if method == "wallet":
        if company == "wallet":
            return "MP", COMMISSION_MP_WALLET, "Mercado Pago, dinero en cuenta"
        if company == "modo":
            rate_info = CARD_RATES_BY_INSTALLMENTS.get(installments if installments > 1 else 1)
            if rate_info:
                rate, label = rate_info
                return "MODO", rate, f"MODO, {label} (misma comisión que débito/crédito)"
            return "MODO", None, f"MODO, {installments} cuotas (comisión no configurada)"
        return "MP", None, f"Billetera '{company or 'desconocida'}' (comisión no configurada)"

    if method == "ticket":
        return "", None, f"Ticket/{company or 'efectivo'} (comisión no configurada)"

    if method == "custom" or gateway == "offline":
        return "", COMMISSION_OFFLINE, "A convenir / pago manual"

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
