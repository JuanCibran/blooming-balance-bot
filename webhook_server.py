import logging
from aiohttp import web
from tiendanube_client import get_order, map_order_to_row
from sheets_writer import append_row

logger = logging.getLogger(__name__)


async def handle_tiendanube_webhook(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    event = payload.get("event", "")
    order_id = str(payload.get("id", ""))

    logger.info(f"Webhook recibido: event={event} order_id={order_id}")

    # Solo procesar órdenes pagadas
    if event not in ("order/paid", "order/created"):
        return web.Response(status=200, text="ignored")

    try:
        order = await get_order(order_id)
        row = map_order_to_row(order)
        append_row(row)
        logger.info(f"Orden {order_id} cargada en Sheet.")
    except Exception as e:
        logger.error(f"Error procesando orden {order_id}: {e}", exc_info=True)
        return web.Response(status=500, text="Error interno")

    return web.Response(status=200, text="ok")


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/webhook/tiendanube", handle_tiendanube_webhook)
    app.router.add_get("/health", lambda r: web.Response(text="ok"))
    return app
