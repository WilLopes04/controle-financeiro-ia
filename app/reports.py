import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict

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

    dia_pagamento = min(dia_vencimento, ultimo_dia_mes)

    return datetime(
        mes_fatura.year,
        mes_fatura.month,
        dia_pagamento
    )


def gerar_planilha(mes_especifico=None):
    sheet_empresa_id, sheet_pessoal_id = obter_ids_planilhas()
    resultado = db.execute("SELECT * FROM transacoes")
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

        if mes_especifico and nome_mes != mes_especifico:
            continue

        dados_google_emp_linhas = []
        dados_google_pes_linhas = []

        entradas_emp = 0
        saidas_emp = 0
        entradas_pes = 0
        saidas_pes = 0

        resumo_categoria_emp = defaultdict(float)
        resumo_categoria_pes = defaultdict(float)

        resumo_cartao_emp = defaultdict(float)
        resumo_cartao_pes = defaultdict(float)

        for linha in dados:

            data_transacao = datetime.strptime(
                linha[1],
                "%Y-%m-%d"
            )

            if data_transacao.month != num_mes:
                continue

            linha_google = [
                linha[0],   # ID da transação no Turso
                linha[1],   # Data
                linha[3],   # Tipo movimento
                linha[4],   # Categoria
                linha[5],   # Forma de pagamento
                linha[6],   # Descrição
                linha[7],   # Valor
                linha[8],   # Parcela atual
                linha[9],   # Total de parcelas
                False       # Coluna Excluir
            ]

            tipo_conta = linha[2].lower()
            tipo_movimento = linha[3].lower()
            categoria = linha[4]
            forma_pagamento = linha[5]
            valor = float(linha[7])

            if tipo_conta == "empresa":

                dados_google_emp_linhas.append(linha_google)

                if tipo_movimento == "entrada":
                    entradas_emp += valor
                else:
                    saidas_emp += valor
                    resumo_categoria_emp[categoria] += valor
                    resumo_cartao_emp[forma_pagamento] += valor

            else:

                dados_google_pes_linhas.append(linha_google)

                if tipo_movimento == "entrada":
                    entradas_pes += valor
                else:
                    saidas_pes += valor
                    resumo_categoria_pes[categoria] += valor
                    resumo_cartao_pes[forma_pagamento] += valor

        dados_google_emp = [
            ["Total Entradas:", entradas_emp],
            ["Total Saídas:", saidas_emp],
            ["Saldo:", entradas_emp - saidas_emp],
            [],
            cabecalho
        ] + dados_google_emp_linhas

        dados_google_pes = [
            ["Total Entradas:", entradas_pes],
            ["Total Saídas:", saidas_pes],
            ["Saldo:", entradas_pes - saidas_pes],
            [],
            cabecalho
        ] + dados_google_pes_linhas

        resumo_categoria_emp_google = [
            ["Resumo por Categoria"],
            ["Categoria", "Total"]
        ]

        for categoria, total in resumo_categoria_emp.items():
            resumo_categoria_emp_google.append(
                [categoria, total]
            )

        resumo_cartao_emp_google = [
            ["Resumo por Cartão"],
            ["Cartão", "Total Fatura"]
        ]

        for cartao, total in resumo_cartao_emp.items():
            resumo_cartao_emp_google.append(
                [cartao, total]
            )

        resumo_categoria_pes_google = [
            ["Resumo por Categoria"],
            ["Categoria", "Total"]
        ]

        for categoria, total in resumo_categoria_pes.items():
            resumo_categoria_pes_google.append(
                [categoria, total]
            )

        resumo_cartao_pes_google = [
            ["Resumo por Cartão"],
            ["Cartão", "Total Fatura"]
        ]

        for cartao, total in resumo_cartao_pes.items():
            resumo_cartao_pes_google.append(
                [cartao, total]
            )

        atualizar_aba_completa(
            sheet_empresa_id,
            nome_mes.upper(),
            dados_google_emp,
            resumo_categoria_emp_google,
            resumo_cartao_emp_google
        )

        atualizar_aba_completa(
            sheet_pessoal_id,
            nome_mes.upper(),
            dados_google_pes,
            resumo_categoria_pes_google,
            resumo_cartao_pes_google
        )
