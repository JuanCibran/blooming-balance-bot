import json
from datetime import date
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Sos el asistente de Blooming Essie, una marca de ropa y accesorios argentina.
Tu tarea es extraer datos estructurados de mensajes sobre ventas y gastos del negocio.

Hoy es {today}.

Devolvé SIEMPRE un JSON válido con esta estructura exacta:
{{
  "tipo": "venta" | "gasto" | "reinversion",
  "fecha": "DD/MM/YYYY",
  "descripcion": "nombre del cliente o descripción del gasto",
  "n_orden": número entero o null,
  "precio_unit": número decimal o null,
  "total": número decimal,
  "medio_pago": "TC" | "TRF" | "MP" | null,
  "categoria": string o null,
  "notas": string o null
}}

Reglas:
- Si no se menciona fecha, usá la fecha de hoy.
- Para medios de pago: TC = tarjeta de crédito, TRF = transferencia, MP = Mercado Pago.
- El total siempre es positivo (aunque sea un gasto).
- Si no podés extraer el total, devolvé un error con "error": "no se pudo determinar el monto".
- Solo devolvé el JSON, sin texto adicional.
"""

def parse_message(text: str) -> dict:
    today = date.today().strftime("%d/%m/%Y")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_PROMPT.format(today=today),
        messages=[{"role": "user", "content": text}],
    )

    raw = response.content[0].text.strip()

    # Limpiar posibles bloques de código markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)
