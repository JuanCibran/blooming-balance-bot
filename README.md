# Blooming Essie — cash flow tracker

Telegram bot that logs sales and expenses to Google Sheets without opening any spreadsheet. You send a text message, Claude interprets it, and the row shows up on its own. Tienda Nube orders are captured automatically via webhook.

## How it works

Two ways for data to reach the Sheet:

1. **Telegram** → you write something like `venta María orden 195 $45000 TC` → `parser.py` sends it to Claude Haiku → gets back JSON → written to the Daily Log
2. **Tienda Nube** → a paid order webhook comes in → full order is fetched from the API → written to the Daily Log

The Sheet has 4 tabs: Daily Log, Monthly Summary, Stock, and Cash & Reinvestment.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file with these variables:

```env
TELEGRAM_BOT_TOKEN=
ANTHROPIC_API_KEY=
TIENDANUBE_USER_ID=
TIENDANUBE_ACCESS_TOKEN=
SPREADSHEET_ID=

# local: path to the service account JSON
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Railway: paste the JSON content as a string
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
```

If the Sheet doesn't exist yet, run this once:

```bash
python setup_sheet.py
```

It prints the `SPREADSHEET_ID` and creates all the tabs. Then share the Sheet with the service account email.

To migrate data from the old Excel file, edit `EXCEL_PATH` in `import_excel.py` and run:

```bash
python import_excel.py
```

## Running the bot

```bash
python bot.py
```

Starts the Telegram bot and the webhook server in the same process.

## Message format

There's no strict format — Claude figures out what it can. Some examples:

```
venta María García orden 195 $45000 TC
gasto Correo Argentino $8500
reinversion compra de mercadería $120000 TRF
```

Payment methods: `TC` = credit card, `TRF` = bank transfer, `MP` = Mercado Pago.

## Deploy (Railway)

Configured in `railway.toml`. Use `GOOGLE_CREDENTIALS_JSON` instead of a file path.

The Tienda Nube webhook points to:

```
https://<railway-domain>/webhook/tiendanube
```

`/health` returns `ok` if the server is running.
