from datetime import datetime
from dateutil.relativedelta import relativedelta
import uuid

from app.db import db
from app.reports import calcular_mes_fatura
from app.google_sheets import adicionar_transacao_planilha



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
    id_compra=None,
    aplicar_regra_cartao=True
):

    if data is None:
        data_obj = datetime.now()
    elif isinstance(data, datetime):
        data_obj = data
    else:
        data_obj = datetime.strptime(data, "%Y-%m-%d")

    if aplicar_regra_cartao:
        resultado = db.execute(
            "SELECT nome FROM cartoes"
        )

        cartoes_cadastrados = {
            linha[0].lower()
            for linha in resultado.rows
        }

        if forma_pagamento.lower() in cartoes_cadastrados:
            data_obj = calcular_mes_fatura(
                data_obj,
                forma_pagamento
            )

    data = data_obj.strftime("%Y-%m-%d")

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

    resultado = db.execute("""
        SELECT
            id,
            data,
            tipo_movimento,
            categoria,
            forma_pagamento,
            descricao,
            valor,
            parcela_atual,
            total_parcelas
        FROM transacoes
        WHERE id_compra = ?
        AND parcela_atual = ?
        ORDER BY id DESC
        LIMIT 1
    """, [
        id_compra,
        parcela_atual
    ]).rows

    if resultado:
        linha_planilha = list(resultado[0]) + [False]

        try:
            adicionar_transacao_planilha(
                tipo_conta,
                linha_planilha
            )
        except Exception as erro:
            print(
                "AVISO: transação registrada no banco, "
                f"mas não foi adicionada à planilha: {erro}"
            ) 

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
            id_compra,
            False
        )
