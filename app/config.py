import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "financeiro.db")

PLANILHA_PESSOAL = os.path.join(BASE_DIR, "planilha_pessoal.xlsx")
PLANILHA_EMPRESA = os.path.join(BASE_DIR, "planilha_empresa.xlsx")

NUMEROS_AUTORIZADOS = [
    "whatsapp:+5585988617337",
    "whatsapp:+5585999186449",
    "whatsapp:+5585987168908"
]

TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""