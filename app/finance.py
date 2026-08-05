from datetime import datetime
from dateutil.relativedelta import relativedelta
import uuid

from app.db import db
from app.reports import (
    calcular_mes_fatura,
    gerar_planilha
)

def atualizar_mes(nome_mes):
    gerar_planilha(nome_mes)

def registrar_transacao(
    tipo_conta,
    tipo_movimento,
    categoria,
    forma_pagamento,
    descricao,
    valor,
    data=None,
    parcela_atual=1,
    total_parcelas=1,
    id_compra=None
):

    if data is None:
        data = datetime.now().strftime("%Y-%m-%d")

    if id_compra is None:
        id_compra = str(uuid.uuid4())

    db.execute("""
        INSERT INTO transacoes (
            data,
            tipo_conta,
            tipo_movimento,
            categoria,
            forma_pagamento,
            descricao,
            valor,
            parcela_atual,
            total_parcelas,
            id_compra
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        data,
        tipo_conta,
        tipo_movimento,
        categoria,
        forma_pagamento,
        descricao,
        valor,
        parcela_atual,
        total_parcelas,
        id_compra
    ])

    mes = datetime.strptime(data, "%Y-%m-%d").month

    meses = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro"
   }

    atualizar_mes(meses[mes]) 

# =========================
# REGISTRAR PARCELADO
# =========================

def registrar_parcelado(
    tipo_conta,
    tipo_movimento,
    categoria,
    forma_pagamento,
    descricao,
    valor_total,
    total_parcelas
):
    valor_parcela = valor_total / total_parcelas
    data_base = datetime.now()

    resultado = db.execute("SELECT nome FROM cartoes")
    cartoes_validos = [linha[0] for linha in resultado.rows]

    if forma_pagamento in cartoes_validos:
        data_base = calcular_mes_fatura(data_base, forma_pagamento)

    id_compra = str(uuid.uuid4())

    for i in range(total_parcelas):
        nova_data = data_base + relativedelta(months=i)

        registrar_transacao(
            tipo_conta,
            tipo_movimento,
            categoria,
            forma_pagamento,
            f"{descricao} ({i+1}/{total_parcelas})",
            valor_parcela,
            nova_data.strftime("%Y-%m-%d"),
            i + 1,
            total_parcelas,
            id_compra
        )
