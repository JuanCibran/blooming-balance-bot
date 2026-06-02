"""
Corre este script UNA sola vez para crear el Google Sheet con la misma
estructura que el Excel original.

Uso:
    python setup_sheet.py

Al finalizar imprime el SPREADSHEET_ID que tenés que poner en el .env
"""

import json
import gspread
from google.oauth2 import service_account
from config import GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_CREDENTIALS_JSON

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    if GOOGLE_CREDENTIALS_JSON:
        info = json.loads(GOOGLE_CREDENTIALS_JSON)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES
        )
    return gspread.authorize(creds)


def setup():
    client = get_client()
    wb = client.create("🌸 Blooming Essie — Control")

    # ── Hoja 1: Registro Diario ────────────────────────────────────────────────
    ws1 = wb.sheet1
    ws1.update_title("📋 Registro Diario")

    ws1.update("A1", [["🌸  BLOOMING ESSIE  —  REGISTRO DIARIO DE MOVIMIENTOS"]])
    ws1.update("A2", [["Registrá cada venta y gasto del día • Texto azul = dato a completar"]])
    ws1.update("A3:J3", [[
        "Fecha", "Tipo", "Categoría", "Descripción",
        "Producto/SKU", "n orden", "Precio Unit.", "Total ($)",
        "Medio de pago", "Notas"
    ]])
    ws1.update("A57:J57", [["TOTAL DEL PERÍODO", "", "", "", "", "", "",
                             '=SUMIF(B4:B56,"Venta",H4:H56)+SUMIF(B4:B56,"Gasto",H4:H56)', "", ""]])
    ws1.update("A58:J58", [["", "", "Ventas", '=SUMIF(B4:B56,"Venta",H4:H56)',
                             "Gastos", '=SUMIF(B4:B56,"Gasto",H4:H56)',
                             "Reinversión", '=SUMIF(B4:B56,"Reinversión",H4:H56)',
                             "Balance", "=H57"]])

    # ── Hoja 2: Resumen Mensual ────────────────────────────────────────────────
    ws2 = wb.add_worksheet("📊 Resumen Mensual", rows=20, cols=8)
    ws2.update("A1", [["🌸  BLOOMING ESSIE  —  RESUMEN MENSUAL"]])
    ws2.update("A2:H2", [["Mes", "Ventas ($)", "Costo mercadería",
                           "Gastos operativos", "Reinversión",
                           "Ganancia Bruta", "Ganancia Neta", "% Margen"]])
    meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    for i, mes in enumerate(meses, start=3):
        ws2.update(f"A{i}:H{i}", [[mes, 0, 0, 0, 0,
                                    f"=B{i}-C{i}", f"=F{i}-D{i}-E{i}",
                                    f"=IFERROR(G{i}/B{i},0)"]])

    # ── Hoja 3: Stock ─────────────────────────────────────────────────────────
    ws3 = wb.add_worksheet("📦 Stock", rows=40, cols=10)
    ws3.update("A1", [["🌸  BLOOMING ESSIE  —  CONTROL DE STOCK"]])
    ws3.update("A2:J2", [["SKU", "Producto", "Categoría", "Talle/Color",
                           "Stock inicial", "Entradas", "Salidas", "Stock actual",
                           "Precio costo", "Precio venta"]])
    stock_inicial = [
        ["REM-FL-S", "Remera floral",        "Ropa",        "S / Rosa",       10, 0, 2, "=E3+F3-G3",   2200, 3500],
        ["REM-FL-M", "Remera floral",        "Ropa",        "M / Rosa",        8, 0, 2, "=E4+F4-G4",   2200, 3500],
        ["REM-FL-L", "Remera floral",        "Ropa",        "L / Rosa",        5, 0, 0, "=E5+F5-G5",   2200, 3500],
        ["ACC-AR-D1","Aros dorados pequeños","Accesorios",  "Único / Dorado", 20, 0, 3, "=E6+F6-G6",    800, 1800],
        ["ACC-CO-R1","Collar perlas rosas",  "Accesorios",  "Único / Rosa",   15, 0, 0, "=E7+F7-G7",    950, 2200],
        ["BLS-LN-M", "Blusa lino beige",     "Ropa",        "M / Beige",       6, 0, 0, "=E8+F8-G8",   3100, 5500],
        ["FLD-FL-S", "Falda flores",         "Ropa",        "S / Multicolor",  4, 0, 0, "=E9+F9-G9",   2800, 4900],
    ]
    ws3.update("A3:J9", stock_inicial)

    # ── Hoja 4: Caja & Reinversión ─────────────────────────────────────────────
    ws4 = wb.add_worksheet("💰 Caja & Reinversión", rows=30, cols=6)
    ws4.update("A1", [["🌸  BLOOMING ESSIE  —  CAJA Y PLAN DE REINVERSIÓN"]])
    ws4.update("A2", [["ESTADO DE CAJA"]])
    ws4.update("A3:F6", [
        ["Saldo inicial del mes",    "", "", "", "", 0],
        ["(+) Total ventas del mes", "", "", "", "",
         "=SUMIF('📋 Registro Diario'!B4:B56,\"Venta\",'📋 Registro Diario'!H4:H56)"],
        ["(-) Total gastos del mes", "", "", "", "",
         "=SUMIF('📋 Registro Diario'!B4:B56,\"Gasto\",'📋 Registro Diario'!H4:H56)"],
        ["(-) Reinversión",          "", "", "", "",
         "=SUMIF('📋 Registro Diario'!B4:B56,\"Reinversión\",'📋 Registro Diario'!H4:H56)"],
    ])

    print(f"\n✅ Google Sheet creado exitosamente.")
    print(f"📋 Nombre: 🌸 Blooming Essie — Control")
    print(f"🔑 SPREADSHEET_ID: {wb.id}")
    print(f"\nAgregá esto a tu .env:")
    print(f"SPREADSHEET_ID={wb.id}")
    print(f"\nY compartí el Sheet con el email de tu service account.")


if __name__ == "__main__":
    setup()
