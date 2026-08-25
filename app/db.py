import os
from contextvars import ContextVar

from dotenv import load_dotenv
from libsql_client import create_client_sync

from app.clients import obter_cliente

from app.schema import inicializar_banco

load_dotenv()


# Guarda qual cliente está sendo atendido durante a mensagem atual.
cliente_atual = ContextVar("cliente_atual", default=None)


# Reaproveita conexões já abertas.
conexoes = {}


def preparar_url(url: str) -> str:
    if not url:
        raise RuntimeError("URL do Turso não configurada.")

    return url.replace("libsql://", "https://")


def selecionar_cliente(numero_telefone: str):
    """
    Identifica o cliente pelo telefone e o mantém selecionado
    durante o processamento da mensagem.
    """
    cliente = obter_cliente(numero_telefone)

    if not cliente:
        return None

    cliente_atual.set(cliente)
    return cliente



def obter_conexao():
    """
    Retorna a conexão Turso correspondente ao cliente selecionado.
    Se nenhum cliente tiver sido selecionado, usa o banco principal.
    """
    cliente = cliente_atual.get()

    if cliente:
        url = cliente.get("turso_url")
        token = cliente.get("turso_token")
    else:
        url = os.getenv("TURSO_DATABASE_URL")
        token = os.getenv("TURSO_AUTH_TOKEN")
        
    url = (url or "").strip()
    token = (token or "").strip()
    
    if not url or not token:
        raise RuntimeError("Banco Turso do cliente não configurado.")

    chave = (url, token)

    if chave not in conexoes:
        nova_conexao = create_client_sync(
            url=preparar_url(url),
            auth_token=token
        )

        inicializar_banco(nova_conexao)

        conexoes[chave] = nova_conexao

    return conexoes[chave]


class BancoDinamico:
    """
    Mantém compatibilidade com os outros arquivos.

    Quando finance.py executar db.execute(...), esta classe escolhe
    automaticamente o banco do cliente que enviou a mensagem.
    """

    def execute(self, *args, **kwargs):
        conexao = obter_conexao()
        return conexao.execute(*args, **kwargs)

    def batch(self, *args, **kwargs):
        conexao = obter_conexao()
        return conexao.batch(*args, **kwargs)

    def close(self):
        for conexao in conexoes.values():
            conexao.close()


db = BancoDinamico()
