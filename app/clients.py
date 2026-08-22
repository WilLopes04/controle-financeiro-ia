import os


def normalizar_telefone(numero: str) -> str:
    """
    Mantém somente os números do telefone.
    Exemplo: +55 (85) 99999-9999 -> 5585999999999
    """
    return "".join(caractere for caractere in str(numero) if caractere.isdigit())


CLIENTES = {
    normalizar_telefone(os.getenv("TELEFONE_CLIENTE_PRINCIPAL", "")): {
        "nome": "Cliente principal",
        "turso_url": os.getenv("TURSO_DATABASE_URL"),
        "turso_token": os.getenv("TURSO_AUTH_TOKEN"),
        "sheet_empresa_id": os.getenv("SHEET_EMPRESA_ID"),
        "sheet_pessoal_id": os.getenv("SHEET_PESSOAL_ID"),
    },

    normalizar_telefone(os.getenv("TELEFONE_JVSOTERO", "")): {
        "nome": "JV Sotero",
        "turso_url": os.getenv("TURSO_DATABASE_URL_JVSOTERO"),
        "turso_token": os.getenv("TURSO_AUTH_TOKEN_JVSOTERO"),
        "sheet_empresa_id": os.getenv("SHEET_EMPRESA_ID_JVSOTERO"),
        "sheet_pessoal_id": os.getenv("SHEET_PESSOAL_ID_JVSOTERO"),
    },
}


# Remove cadastros cujo telefone ainda não foi configurado.
CLIENTES.pop("", None)


def obter_cliente(numero: str):
    telefone = normalizar_telefone(numero)
    return CLIENTES.get(telefone)
