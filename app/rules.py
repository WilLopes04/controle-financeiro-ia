from app.db import db

def listar_regras():

    rows = db.execute("""
        SELECT padrao, tipo_conta, categoria
        FROM regras
        ORDER BY padrao
    """).rows

    return rows


def salvar_regra(padrao: str, tipo_conta: str, categoria: str = None):

    padrao = (padrao or "").strip().lower()
    tipo_conta = (tipo_conta or "").strip().lower()
    categoria = (categoria or "").strip().lower() if categoria else None


    db.execute("""
        INSERT INTO regras (padrao, tipo_conta, categoria)
        VALUES (?, ?, ?)
        ON CONFLICT(padrao) DO UPDATE SET
            tipo_conta=excluded.tipo_conta,
            categoria=excluded.categoria
    """, [
        padrao,
        tipo_conta,
        categoria
    ])


def aplicar_regras(texto: str):
    t = (texto or "").lower()
    regras = listar_regras()

    for padrao, tipo_conta, categoria in regras:
        if padrao and padrao in t:
            out = {"tipo_conta": tipo_conta}
            if categoria:
                out["categoria"] = categoria
            return out

