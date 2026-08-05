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

    resultado = db.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM transacoes
        WHERE tipo_conta = ?
        AND tipo_movimento = 'saida'
        AND forma_pagamento = ?
    """, [
        tipo_conta,
        nome_cartao
    ]).rows

    return resultado[0][0]


def calcular_saldo(tipo_conta):

    registros = db.execute("""
        SELECT tipo_movimento, valor
        FROM transacoes
        WHERE LOWER(tipo_conta) = LOWER(?)
    """, [tipo_conta]).rows

    saldo = 0

    for tipo_movimento, valor in registros:
        if tipo_movimento.lower() == "entrada":
            saldo += valor
        else:
            saldo -= valor

    return saldo