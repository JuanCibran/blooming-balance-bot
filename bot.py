import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN
from parser import parse_message
from sheets_writer import append_movimiento

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

MEDIO_PAGO_LABELS = {
    "TC": "Tarjeta de crédito",
    "TRF": "Transferencia",
    "MP": "Mercado Pago",
}

TIPO_EMOJI = {
    "venta": "💰",
    "gasto": "🧾",
    "reinversion": "🔄",
}


def _format_confirmation(data: dict) -> str:
    emoji = TIPO_EMOJI.get(data["tipo"], "📋")
    tipo = data["tipo"].capitalize()
    fecha = data.get("fecha", "—")
    descripcion = data.get("descripcion", "—")
    total = f"${data['total']:,.2f}".replace(",", ".")
    medio = MEDIO_PAGO_LABELS.get(data.get("medio_pago", ""), data.get("medio_pago") or "—")
    orden = f"Orden #{data['n_orden']}" if data.get("n_orden") else None
    notas = data.get("notas")

    lines = [
        f"{emoji} *{tipo} registrada*",
        f"📅 {fecha}",
        f"👤 {descripcion}",
    ]
    if orden:
        lines.append(f"🔢 {orden}")
    lines.append(f"💵 {total}")
    if data.get("medio_pago"):
        lines.append(f"💳 {medio}")
    if notas:
        lines.append(f"📝 {notas}")

    return "\n".join(lines)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    await update.message.reply_text("⏳ Procesando...")

    try:
        data = parse_message(text)

        if "error" in data:
            await update.message.reply_text(
                f"❌ No pude procesar el mensaje: {data['error']}\n\n"
                "Probá con algo como:\n"
                "• _venta María García orden 195 $45000 TC_\n"
                "• _gasto Correo Argentino $8500_",
                parse_mode="Markdown",
            )
            return

        append_movimiento(data)
        confirmation = _format_confirmation(data)
        await update.message.reply_text(f"✅ {confirmation}", parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Error procesando mensaje: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Ocurrió un error inesperado. Revisá los logs."
        )


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("Bot iniciado.")
    app.run_polling()


if __name__ == "__main__":
    main()
