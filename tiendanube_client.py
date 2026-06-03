import aiohttp
from config import TIENDANUBE_USER_ID, TIENDANUBE_ACCESS_TOKEN

BASE_URL = f"https://api.tiendanube.com/v1/{TIENDANUBE_USER_ID}"
HEADERS = {
    "Authentication": f"bearer {TIENDANUBE_ACCESS_TOKEN}",
    "User-Agent": "Blooming Essie Bot (bloomingessie@gmail.com)",
    "Content-Type": "application/json",
}

PAYMENT_METHOD_MAP = {
    "credit_card": "TC",
    "debit_card": "TC",
    "transfer": "TRF",
    "bank_transfer": "TRF",
    "mercadopago": "MP",
    "mercado_pago": "MP",
    "account_money": "MP",
}


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

    # Medio de pago
    gateway = (order.get("payment_details") or {}).get("method") or ""
    medio = PAYMENT_METHOD_MAP.get(gateway.lower(), "")

    return [
        fecha,       # Fecha
        "Venta",     # Tipo
        "",          # Categoría
        nombre,      # Descripción (nombre cliente)
        "",          # Producto/SKU
        n_orden,     # n orden
        "",          # Precio Unit.
        total,       # Total ($)
        medio,       # Medio de pago
        "",          # Notas
    ]
