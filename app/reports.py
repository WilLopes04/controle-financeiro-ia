import calendar
from datetime import datetime

from dateutil.relativedelta import relativedelta

from app.db import db
from app.google_sheets import (
    atualizar_aba_completa,
    obter_ids_planilhas
)


def calcular_mes_fatura(data_compra, nome_cartao):

    resultado = db.execute("""
        SELECT dia_fechamento, dia_vencimento
        FROM cartoes
        WHERE LOWER(nome) = LOWER(?)
    """, [nome_cartao]).rows

    if not resultado:
        return data_compra

    dia_fechamento = int(resultado[0][0])
    dia_vencimento = int(resultado[0][1])

    # Depois do fechamento, a compra pertence à fatura seguinte.
    if data_compra.day > dia_fechamento:
        mes_fatura = data_compra + relativedelta(months=1)
    else:
        mes_fatura = data_compra

    # Evita datas inválidas, como dia 30 em fevereiro.
    ultimo_dia_mes = calendar.monthrange(
        mes_fatura.year,
        mes_fatura.month
    )[1]

    dia_pagamento = min(
        dia_vencimento,
        ultimo_dia_mes
    )

    return datetime(
        mes_fatura.year,
        mes_fatura.month,
        dia_pagamento
    )


def gerar_planilha(mes_especifico=None):

    sheet_empresa_id, sheet_pessoal_id = (
        obter_ids_planilhas()
    )

    resultado = db.execute(
        "SELECT * FROM transacoes"
    )

    dados = resultado.rows

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

    cabecalho = [
        "ID",
        "Data",
        "Tipo Movimento",
        "Categoria",
        "Forma Pagamento",
        "Descrição",
        "Valor",
        "Parcela",
        "Total Parcelas",
        "Excluir"
    ]

    for num_mes, nome_mes in meses.items():

        if (
            mes_especifico
            and nome_mes != mes_especifico
        ):
            continue

        dados_google_emp_linhas = []
        dados_google_pes_linhas = []

        for linha in dados:

            data_transacao = datetime.strptime(
                linha[1],
                "%Y-%m-%d"
            )

            if data_transacao.month != num_mes:
                continue

            linha_google = [
                linha[0],   # ID
                linha[1],   # Data
                linha[3],   # Tipo movimento
                linha[4],   # Categoria
                linha[5],   # Forma de pagamento
                linha[6],   # Descrição
                linha[7],   # Valor
                linha[8],   # Parcela atual
                linha[9],   # Total de parcelas
                False       # Excluir
            ]

            tipo_conta = str(
                linha[2]
            ).lower()

            if tipo_conta == "empresa":
                dados_google_emp_linhas.append(
                    linha_google
                )
            else:
                dados_google_pes_linhas.append(
                    linha_google
                )

dados_google_emp = [
    [
        "Total Entradas:",
        '=SUMIFS(G6:G;C6:C;"entrada";J6:J;"<>TRUE")'
    ],
    [
        "Total Saídas:",
        '=SUMIFS(G6:G;C6:C;"saida";J6:J;"<>TRUE")'
    ],
    ["Saldo:", "=B1-B2"],
    [],
    cabecalho
] + dados_google_emp_linhas

dados_google_pes = [
    [
        "Total Entradas:",
        '=SUMIFS(G6:G;C6:C;"entrada";J6:J;"<>TRUE")'
    ],
    [
        "Total Saídas:",
        '=SUMIFS(G6:G;C6:C;"saida";J6:J;"<>TRUE")'
    ],
    ["Saldo:", "=B1-B2"],
    [],
    cabecalho
] + dados_google_pes_linhas

        atualizar_aba_completa(
            sheet_empresa_id,
            nome_mes.upper(),
            dados_google_emp
        )

        atualizar_aba_completa(
            sheet_pessoal_id,
            nome_mes.upper(),
            dados_google_pes
        )
