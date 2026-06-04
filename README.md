# Blooming Essie — control de caja

Bot de Telegram para registrar ventas y gastos en Google Sheets sin abrir ninguna planilla. Mandás un mensaje de texto, Claude lo interpreta, y aparece la fila cargada sola. Las órdenes de Tienda Nube se capturan automáticamente via webhook.

## Cómo funciona

Hay dos caminos para que un dato llegue al Sheet:

1. **Telegram** → escribís algo como `venta María orden 195 $45000 TC` → `parser.py` se lo manda a Claude Haiku → devuelve JSON → se escribe en el Registro Diario
2. **Tienda Nube** → llega un webhook de orden pagada → se consulta la orden completa en la API → se escribe en el Registro Diario

El Sheet tiene 4 hojas: Registro Diario, Resumen Mensual, Stock y Caja & Reinversión.

## Setup

```bash
pip install -r requirements.txt
```

Crear `.env` con estas variables:

```env
TELEGRAM_BOT_TOKEN=
ANTHROPIC_API_KEY=
TIENDANUBE_USER_ID=
TIENDANUBE_ACCESS_TOKEN=
SPREADSHEET_ID=

# local: path al JSON del service account
GOOGLE_APPLICATION_CREDENTIALS=/ruta/al/service-account.json

# Railway: pegar el contenido del JSON como string
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
```

Si el Sheet todavía no existe, correr esto una sola vez:

```bash
python setup_sheet.py
```

Imprime el `SPREADSHEET_ID` y crea todas las hojas. Después acordarse de compartir el Sheet con el email del service account.

Para migrar datos del Excel viejo, editar `EXCEL_PATH` en `import_excel.py` y correr:

```bash
python import_excel.py
```

## Correr el bot

```bash
python bot.py
```

Levanta el bot de Telegram y el servidor de webhooks en el mismo proceso.

## Formato de mensajes

No hay un formato estricto, Claude deduce lo que puede. Algunos ejemplos:

```
venta María García orden 195 $45000 TC
gasto Correo Argentino $8500
reinversion compra de mercadería $120000 TRF
```

Medios de pago: `TC` = tarjeta de crédito, `TRF` = transferencia, `MP` = Mercado Pago.

## Deploy (Railway)

Configurado en `railway.toml`. Usar `GOOGLE_CREDENTIALS_JSON` en lugar del path al archivo.

El webhook de Tienda Nube va a:

```
https://<dominio-railway>/webhook/tiendanube
```

`/health` devuelve `ok` si el servidor está andando.
