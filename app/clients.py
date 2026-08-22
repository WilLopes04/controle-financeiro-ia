import os

from dotenv import load_dotenv


load_dotenv()


def normalizar_telefone(numero: str) -> str:
    """
    Mantém somente os números do telefone.
    Exemplo: +55 (85) 99999-9999 -> 5585999999999
    """
    return "".join(
        caractere
        for caractere in str(numero)
        if caractere.isdigit()
    )


def cadastrar_telefones(clientes, telefones, configuracao):
    """
    Relaciona vários telefones ao mesmo cliente.
    Os números devem estar separados por vírgula no Render.
    """
    for numero in telefones.split(","):
        telefone = normalizar_telefone(numero)

        if telefone:
            clientes[telefone] = configuracao


CLIENTES = {}


cliente_principal = {
    "nome": "Cliente principal",
    "turso_url": os.getenv("TURSO_DATABASE_URL"),
    "turso_token": os.getenv("TURSO_AUTH_TOKEN"),
    "sheet_empresa_id": os.getenv("SHEET_EMPRESA_ID"),
    "sheet_pessoal_id": os.getenv("SHEET_PESSOAL_ID"),
}

cadastrar_telefones(
    CLIENTES,
    os.getenv("TELEFONES_CLIENTE_PRINCIPAL", ""),
    cliente_principal
)


cliente_jvsotero = {
    "nome": "JV Sotero",
    "turso_url": os.getenv("TURSO_DATABASE_URL_JVSOTERO"),
    "turso_token": os.getenv("TURSO_AUTH_TOKEN_JVSOTERO"),
    "sheet_empresa_id": os.getenv("SHEET_EMPRESA_ID_JVSOTERO"),
    "sheet_pessoal_id": os.getenv("SHEET_PESSOAL_ID_JVSOTERO"),
}

cadastrar_telefones(
    CLIENTES,
    os.getenv("TELEFONES_JVSOTERO", ""),
    cliente_jvsotero
)


def obter_cliente(numero: str):
    telefone = normalizar_telefone(numero)
    return CLIENTES.get(telefone)
