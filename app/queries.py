from app.db import db


def total_entradas(tipo_conta):

    resultado = db.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM transacoes
        WHERE tipo_conta = ?
        AND tipo_movimento = 'entrada'
    """, [tipo_conta]).rows

    return resultado[0][0]


def total_saidas(tipo_conta):

    resultado = db.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM transacoes
        WHERE tipo_conta = ?
        AND tipo_movimento = 'saida'
    """, [tipo_conta]).rows

    return resultado[0][0]


def fatura_cartao(nome_cartao, tipo_conta):
    from datetime import datetime

    agora = datetime.now()
    ano = agora.year
    mes = agora.month

    inicio_mes = f"{ano}-{mes:02d}-01"

    if mes == 12:
        inicio_proximo_mes = f"{ano + 1}-01-01"
    else:
        inicio_proximo_mes = f"{ano}-{mes + 1:02d}-01"

    resultado = db.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM transacoes
        WHERE LOWER(tipo_conta) = LOWER(?)
          AND LOWER(tipo_movimento) = 'saida'
          AND LOWER(forma_pagamento) = LOWER(?)
          AND data >= ?
          AND data < ?
    """, [
        tipo_conta,
        nome_cartao,
        inicio_mes,
        inicio_proximo_mes
    ]).rows

    return resultado[0][0]


def calcular_saldo(tipo_conta):
    from datetime import datetime

    agora = datetime.now()
    ano = agora.year
    mes = agora.month

    inicio_mes = f"{ano}-{mes:02d}-01"

    if mes == 12:
        inicio_proximo_mes = f"{ano + 1}-01-01"
    else:
        inicio_proximo_mes = f"{ano}-{mes + 1:02d}-01"

    registros = db.execute("""
        SELECT tipo_movimento, valor
        FROM transacoes
        WHERE LOWER(tipo_conta) = LOWER(?)
          AND data >= ?
          AND data < ?
    """, [tipo_conta, inicio_mes, inicio_proximo_mes]).rows

    saldo = 0

    for tipo_movimento, valor in registros:
        if tipo_movimento.lower() == "entrada":
            saldo += valor
        else:
            saldo -= valor

    return saldo