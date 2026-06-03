import gspread
import json
import os
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

google_creds = json.loads(
    os.environ["GOOGLE_CREDENTIALS_JSON"] 
)

creds = Credentials.from_service_account_file(
    google_creds,
    scopes=SCOPES
)

client = gspread.authorize(creds)

SHEET_EMPRESA_ID = "1kZKqE0_KNa8ER8nYMsvVHajnh6Bs5nlstw_g-as1NiY"
SHEET_PESSOAL_ID = "1ezhvVbaNYAZXWDKdLB9R_u19TcmcyPAVUTGlHR3i574"

empresa_sheet = client.open_by_key(SHEET_EMPRESA_ID)
pessoal_sheet = client.open_by_key(SHEET_PESSOAL_ID)

def obter_planilha(planilha_id):

    if planilha_id == SHEET_EMPRESA_ID:
        return empresa_sheet

    return pessoal_sheet


def atualizar_aba(planilha_id, nome_aba, dados):
    planilha = obter_planilha(planilha_id)
    aba = planilha.worksheet(nome_aba)

    aba.clear()

    if dados:
        aba.update("A1", dados)

def atualizar_resumo_categoria(
    sheet_id,
    nome_aba,
    resumo
):

    planilha = obter_planilha(sheet_id)

    aba = planilha.worksheet(nome_aba)

    aba.update("J2", resumo)


def atualizar_resumo_cartao(
    sheet_id,
    nome_aba,
    resumo
):

    planilha = obter_planilha(sheet_id)

    aba = planilha.worksheet(nome_aba)

    aba.update("M2", resumo)