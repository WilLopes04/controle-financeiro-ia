from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import uuid

from app.db import db
from app.reports import calcular_mes_fatura
from app.google_sheets import (
    adicionar_transacao_planilha,
    obter_transacoes_manuais,
    preencher_id_transacao_manual
)



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

def sincronizar_novas_transacoes_planilha():
    """
    Insere no Turso somente linhas manuais sem ID.
    Depois preenche o ID na mesma linha da planilha.
    """

    transacoes = obter_transacoes_manuais()

    resultado = {
        "encontradas": len(transacoes),
        "inseridas": 0,
        "recuperadas": 0,
        "erros": []
    }

    for item in transacoes:
        referencia = (
            f"{item['nome_aba']}!"
            f"A{item['numero_linha']}"
        )

        try:
            valor_data = item["data"]
            texto_data = str(valor_data).strip()
            data_obj = None

            # O Google Sheets pode retornar datas como
            # número serial, por exemplo 46259.
            try:
                numero_data = float(
                    texto_data.replace(",", ".")
                )

                data_obj = (
                    datetime(1899, 12, 30)
                    + timedelta(days=numero_data)
                )
            except ValueError:
                for formato in (
                    "%Y-%m-%d",
                    "%d/%m/%Y"
                ):
                    try:
                        data_obj = datetime.strptime(
                            texto_data,
                            formato
                        )
                        break
                    except ValueError:
                        continue

            if data_obj is None:
                raise ValueError(
                    f"data inválida: {texto_data}"
                )

            data = data_obj.strftime("%Y-%m-%d")

            tipo_movimento = str(
                item["tipo_movimento"]
            ).strip().lower()

            if tipo_movimento == "saída":
                tipo_movimento = "saida"

            if tipo_movimento not in {
                "entrada",
                "saida"
            }:
                raise ValueError(
                    "tipo de movimento deve ser entrada ou saida"
                )

            valor_original = item["valor"]

            if isinstance(valor_original, (int, float)):
                valor = float(valor_original)
            else:
                texto_valor = (
                    str(valor_original)
                    .strip()
                    .replace("R$", "")
                    .replace(" ", "")
                )

                if "," in texto_valor:
                    texto_valor = (
                        texto_valor
                        .replace(".", "")
                        .replace(",", ".")
                    )

                valor = float(texto_valor)

            parcela_atual = int(
                float(
                    str(item["parcela_atual"])
                    .strip()
                    .replace(",", ".")
                )
            )

            total_parcelas = int(
                float(
                    str(item["total_parcelas"])
                    .strip()
                    .replace(",", ".")
                )
            )

            # Identificador determinístico:
            # evita duplicação se o banco registrar e o Google falhar.
            chave_manual = (
                f"{item['planilha_id']}|"
                f"{item['nome_aba']}|"
                f"{item['numero_linha']}|"
                f"{data}|"
                f"{item['descricao']}|"
                f"{valor}"
            )

            id_compra = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    chave_manual
                )
            )

            existente = db.execute("""
                SELECT id
                FROM transacoes
                WHERE id_compra = ?
                LIMIT 1
            """, [id_compra]).rows

            if existente:
                id_transacao = existente[0][0]
                resultado["recuperadas"] += 1
            else:
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
                    item["tipo_conta"],
                    tipo_movimento,
                    str(item["categoria"]).strip(),
                    str(item["forma_pagamento"]).strip(),
                    str(item["descricao"]).strip(),
                    valor,
                    parcela_atual,
                    total_parcelas,
                    id_compra
                ])

                registro = db.execute("""
                    SELECT id
                    FROM transacoes
                    WHERE id_compra = ?
                    LIMIT 1
                """, [id_compra]).rows

                if not registro:
                    raise RuntimeError(
                        "o banco não retornou o ID criado"
                    )

                id_transacao = registro[0][0]
                resultado["inseridas"] += 1

            preencher_id_transacao_manual(
                item["planilha_id"],
                item["nome_aba"],
                item["numero_linha"],
                id_transacao
            )

        except Exception as erro:
            resultado["erros"].append(
                f"{referencia}: {erro}"
            )

    return resultado
