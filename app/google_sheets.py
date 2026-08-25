import json
import os

import gspread
from google.oauth2.service_account import Credentials

from app.db import cliente_atual


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


google_creds = json.loads(
    os.environ["GOOGLE_CREDENTIALS_JSON"]
)

creds = Credentials.from_service_account_info(
    google_creds,
    scopes=SCOPES
)

google_client = gspread.authorize(creds)


# Guarda planilhas que já foram abertas para evitar conexões repetidas.
planilhas_abertas = {}


def obter_ids_planilhas():
    """
    Retorna os IDs das planilhas do cliente selecionado.

    Se nenhum cliente tiver sido selecionado, utiliza as variáveis
    principais para manter compatibilidade com o sistema atual.
    """
    cliente = cliente_atual.get()

    if cliente:
        empresa_id = cliente.get("sheet_empresa_id")
        pessoal_id = cliente.get("sheet_pessoal_id")
    else:
        empresa_id = os.getenv("SHEET_EMPRESA_ID")
        pessoal_id = os.getenv("SHEET_PESSOAL_ID")

    if not empresa_id or not pessoal_id:
        raise RuntimeError(
            "IDs das planilhas do cliente não foram configurados."
        )

    return empresa_id, pessoal_id


def obter_planilha(planilha_id):
    if planilha_id not in planilhas_abertas:
        planilhas_abertas[planilha_id] = google_client.open_by_key(
            planilha_id
        )

    return planilhas_abertas[planilha_id]


def atualizar_aba(planilha_id, nome_aba, dados):
    planilha = obter_planilha(planilha_id)
    aba = planilha.worksheet(nome_aba)

    aba.clear()

    if dados:
        aba.update("A1", dados)


def atualizar_resumo_categoria(sheet_id, nome_aba, resumo):
    planilha = obter_planilha(sheet_id)
    aba = planilha.worksheet(nome_aba)
    aba.update("L2", resumo)


def atualizar_resumo_cartao(sheet_id, nome_aba, resumo):
    planilha = obter_planilha(sheet_id)
    aba = planilha.worksheet(nome_aba)
    aba.update("O2", resumo)
