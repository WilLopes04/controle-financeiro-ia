from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import os
import requests
import json
import traceback
import io


APP_VERSION = "MAIN_ATUAL_2026.08.05"
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

from app.finance import (
    registrar_transacao,
    registrar_parcelado
)

from app.queries import (
    calcular_saldo,
    fatura_cartao
)

from app.db import selecionar_cliente, db

def log(*args):
    """
    Log seguro: nunca derruba o app por UnicodeEncodeError.
    """
    try:
        print(*args, flush=True)
    except UnicodeEncodeError:
        safe = " ".join(str(a) for a in args).encode("utf-8", "backslashreplace").decode("utf-8", "ignore")
        print(safe, flush=True)


# Regras/memória (se não existirem, não quebra)

from app.rules import aplicar_regras, salvar_regra, listar_regras

REGRAS_HABILITADAS = True

app = FastAPI()




# CONFIG WHATSAPP

VERIFY_TOKEN = "wilson123"
PHONE_NUMBER_ID = "952786974592454"
GRAPH_VERSION = "v22.0"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "").strip()

# CONFIG OPENAI

def listar_cartoes_cliente():
    """
    Consulta os cartões do cliente atualmente selecionado.
    """
    try:
        resultado = db.execute(
            "SELECT nome FROM cartoes ORDER BY nome"
        )

        return [linha[0] for linha in resultado.rows]

    except Exception as erro:
        log("Erro ao consultar cartões:", str(erro))
        return []




# ROTAS (Swagger) FORAM PARA OS TESTES DO SERVIDOR LOCAL

@app.get("/")
def home():
    return {"status": "Servidor financeiro rodando"}




# FUNÇÕES WHATSAPP

def enviar_whatsapp(to: str, texto: str):
    if not WHATSAPP_TOKEN:
        log("ERRO: WHATSAPP_TOKEN não configurado.")
        return None

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": texto},
    }

    r = requests.post(url, headers=headers, json=payload, timeout=20)
    if r.status_code >= 300:
        log("ERRO ao enviar WhatsApp:", r.status_code, r.text)
    return r


def obter_media_url(media_id: str) -> str:
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()["url"]


def baixar_media(media_url: str) -> bytes:
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    r = requests.get(media_url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.content


def transcrever_audio_openai(audio_bytes: bytes) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não configurada no ambiente do servidor.")

    client = OpenAI(api_key=api_key)

    f = io.BytesIO(audio_bytes)
    f.name = "audio.ogg"

    resp = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=f
    )
    return getattr(resp, "text", "").strip()



# Comandos manuais + aprender

def interpretar_comando(msg: str):
    txt = (msg or "").strip()
    low = txt.lower()

    # aprender: tecido = empresa / insumos
    if low.startswith("aprender:"):
        if not REGRAS_HABILITADAS:
            return ("erro", {"texto": "A função de aprendizado ainda não foi ativada no database.py."})

        try:
            payload = txt.split(":", 1)[1].strip()
            left, right = payload.split("=", 1)
            padrao = left.strip().lower()

            tipo_cat = right.strip()
            if "/" in tipo_cat:
                tipo_conta, categoria = [x.strip().lower() for x in tipo_cat.split("/", 1)]
            else:
                tipo_conta, categoria = tipo_cat.strip().lower(), None

            if tipo_conta not in ("empresa", "pessoal"):
                return ("erro", {"texto": "Use tipo_conta: empresa ou pessoal. Ex: aprender: tecido = empresa / insumos"})

            return ("aprender", {"padrao": padrao, "tipo_conta": tipo_conta, "categoria": categoria})
        except Exception:
            return ("erro", {"texto": "Formato: aprender: tecido = empresa / insumos"})

    # SALDO
    if low.startswith("saldo"):
        parts = txt.split()
        tipo = parts[1].lower() if len(parts) > 1 else "empresa"
        return ("saldo", {"tipo_conta": tipo})

    # FATURA
    if low.startswith("fatura"):
        parts = txt.split()
        tipo = parts[1].lower() if len(parts) > 1 else "empresa"

        cartao = " ".join(parts[2:]).strip() if len(parts) > 2 else ""

        if not cartao:
            cartoes = listar_cartoes_cliente()
            cartao = cartoes[0] if cartoes else ""

        return (
            "fatura",
            {
                "tipo_conta": tipo,
                "cartao": cartao
            }
        )
        
    # REGISTRAR (manual)
    if low.startswith("registrar "):
        parts = txt.split()
        if len(parts) < 7:
            return ("erro", {"texto": "Formato: registrar empresa saida farmacia pix Descricao 25.50"})

        tipo_conta = parts[1].lower()
        tipo_movimento = parts[2].lower()
        categoria = parts[3]
        forma = parts[4]
        valor_str = parts[-1].replace(",", ".")
        try:
            valor = float(valor_str)
        except ValueError:
            return ("erro", {"texto": "Valor inválido. Ex: 25.50"})

        descricao = " ".join(parts[5:-1])

        return ("registrar", {
            "tipo_conta": tipo_conta,
            "tipo_movimento": tipo_movimento,
            "categoria": categoria,
            "forma_pagamento": forma,
            "descricao": descricao,
            "valor": valor
        })

    return ("ajuda", {})


# IA: interpretar texto livre

def interpretar_com_ia(texto: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {"acao": "erro", "mensagem": "OPENAI_API_KEY não configurada no ambiente do servidor."}

    try:
        client = OpenAI(api_key=api_key)
        cartoes_validos = listar_cartoes_cliente()
        regras_txt = ""
        
        try:
            regras = listar_regras()

            if regras:
                regras_txt = "Regras salvas (priorize quando bater):\n" + "\n".join(
                    [f"- '{p}' -> {tc} ({cat or 'sem categoria'})" for (p, tc, cat) in regras]
                )
        except Exception as e:
            log("Erro ao carregar regras:", str(e))
            regras_txt = ""

        contexto_empresa = """
Contexto fixo:
- A empresa é uma confecção de roupas femininas.
- Gastos comuns de empresa: tecido, malha, linha, botão, aviamento, etiqueta, zíper, embalagem,
  facção, costureira, oficina, corte, estamparia, bordado, transporte de mercadoria, fornecedor de insumos.
- Se a mensagem contiver esses termos e NÃO mencionar explicitamente "pessoal", tenda a usar tipo_conta="empresa".
- Se a mensagem mencionar explicitamente "pessoal" ou "da empresa", respeite.
"""

        system = f"""
{contexto_empresa}
{regras_txt}

Você é um assistente financeiro. Extraia intenção e dados e devolva APENAS um JSON válido.

SEMPRE inclua o campo "acao" com um destes valores:
- "registrar"
- "registrar_parcelado"
- "saldo"
- "fatura"
- "ajuda"

Regras de campos:
- tipo_conta: "empresa" ou "pessoal" (se não for dito, use sua melhor inferência)
- tipo_movimento: "entrada" ou "saida"
- categoria: se não souber use "outros"
- forma_pagamento: "pix", "debito", "credito" ou um cartão cadastrado em {cartoes_validos}
- Quando a mensagem mencionar um cartão cadastrado, devolva exatamente o nome presente nessa lista.
- descricao: texto curto (se não houver, use algo como "Transação")
- valor: número com ponto

IMPORTANTE: responda SOMENTE JSON puro (sem markdown).
"""

        resp = client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": texto}
            ]
        )

        out = getattr(resp, "output_text", None) or ""
        log("IA raw:", out)

        try:
            return json.loads(out)
        except Exception:
            start = out.find("{")
            end = out.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(out[start:end+1])
            return {"acao": "erro", "mensagem": f"IA não retornou JSON. Retorno: {out[:200]}"}

    except Exception as e:
        log("ERRO OpenAI:", str(e))
        traceback.print_exc()
        return {"acao": "erro", "mensagem": f"Erro OpenAI: {str(e)}"}


def inferir_acao_se_faltar(ia: dict) -> str:
    if "valor_total" in ia and "total_parcelas" in ia:
        return "registrar_parcelado"
    if "valor" in ia:
        return "registrar"
    if "cartao" in ia:
        return "fatura"
    if "tipo_conta" in ia and len(ia.keys()) <= 2:
        return "saldo"
    return "ajuda"



# WEBHOOK WHATSAPP

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Erro na verificação", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request):
    log(f"APP_VERSION={APP_VERSION}")
    data = await request.json()
    log("Webhook recebido")

    try:
        entries = data.get("entry", [])

        if not entries:
            return {"status": "ok"}

        changes_list = entries[0].get("changes",[])
        

        if not changes_list:
            return {"status": "ok"}

        changes = changes_list[0].get("value",[])
        
        messages = changes.get("messages",[])

        if not messages:
            return {"status": "ok"}

        msg_obj = messages[0]

        message_id = msg_obj.get("id")

        log(f"MESSAGE_ID {message_id}")

        # Evita processar a mesma mensagem mais de uma vez
        if message_id:
            if not hasattr(receive_webhook, "ids_processados"):
                receive_webhook.ids_processados = set()

            if message_id in receive_webhook.ids_processados:
                log(f"MENSAGEM DUPLICADA IGNORADA: {message_id}")
                return {"status": "ok"}

            receive_webhook.ids_processados.add(message_id)

            if len(receive_webhook.ids_processados) > 5000:
                receive_webhook.ids_processados.clear()

        from_number = msg_obj.get("from", "")
        log("DIAGNOSTICO - numero recebido pela Meta:", from_number)
        cliente = selecionar_cliente(from_number)

        if not cliente:
            log("Mensagem recebida de número não autorizado.")
            enviar_whatsapp(
                from_number,
                "⚠️ Este número ainda não está autorizado a utilizar o assistente financeiro."
            )
            return {"status": "ok"}

        log("Cliente identificado:", cliente["nome"])
        
        msg_type = msg_obj.get("type", "")
        msg_text = ""

        log("msg_type:", msg_type)

        if msg_type == "text":
            msg_text = msg_obj.get("text", {}).get("body", "") or ""

        elif msg_type == "audio":
            media_id = msg_obj.get("audio", {}).get("id")
            if media_id:
                try:
                    media_url = obter_media_url(media_id)
                    audio_bytes = baixar_media(media_url)
                    msg_text = transcrever_audio_openai(audio_bytes)
                    log("Audio transcrito:", msg_text)
                except Exception as e:
                    log("Falha transcrição:", str(e))
                    enviar_whatsapp(from_number, "❌ Não consegui transcrever o áudio. Pode tentar enviar em texto?")
                    return {"status": "ok"}
            else:
                return {"status": "ok"}
        else:
            return {"status": "ok"}

        msg_text = (msg_text or "").strip()
        if not msg_text:
            return {"status": "ok"}

        log("Texto recebido:", msg_text)

        # aplicar regras locais
        sugestao = {}
        if REGRAS_HABILITADAS and aplicar_regras:
            try:
                sugestao = aplicar_regras(msg_text) or {}
                if sugestao:
                    log("Regras sugeriram:", sugestao)
            except Exception:
                sugestao = {}

        # comandos fixos
        acao, params = interpretar_comando(msg_text)

        # IA
        if acao == "ajuda":
            ia = interpretar_com_ia(msg_text)

            if ia.get("acao") == "erro":
                enviar_whatsapp(from_number, f"⚠️ IA falhou: {ia.get('mensagem')}")
                return {"status": "ok"}

            acao = ia.get("acao") or inferir_acao_se_faltar(ia)
            params = ia

        # aplica sugestão de regra
        if sugestao:
            if sugestao.get("tipo_conta"):
                params["tipo_conta"] = sugestao["tipo_conta"]
            if sugestao.get("categoria") and (params.get("categoria") in (None, "", "outros")):
                params["categoria"] = sugestao["categoria"]

        # Executar
        if acao == "aprender":
            salvar_regra(params["padrao"], params["tipo_conta"], params.get("categoria"))
            enviar_whatsapp(
                from_number,
                f"✅ Aprendi: '{params['padrao']}' -> {params['tipo_conta']} / {params.get('categoria','')}"
            )
            return {"status": "ok"}

        if acao == "saldo":
            tipo = (params.get("tipo_conta") or "empresa").lower()
            saldo = calcular_saldo(tipo)
            enviar_whatsapp(from_number, f"💰 Saldo {tipo}: R$ {saldo:.2f}")

        elif acao == "fatura":
            tipo = (params.get("tipo_conta") or "empresa").lower()
            cartao = params.get("cartao", "Santander")
            total = fatura_cartao(cartao, tipo)
            enviar_whatsapp(from_number, f"💳 Fatura {cartao} ({tipo}): R$ {total:.2f}")

        elif acao == "registrar_parcelado":

            valor_total = params.get("valor_total", params.get("valor", 0))
            total_parcelas = params.get(
                "total_parcelas",
                params.get("parcelas", 1)
            )



            registrar_parcelado(
                (params.get("tipo_conta") or "empresa").lower(),
                (params.get("tipo_movimento") or "saida").lower(),
                params.get("categoria", "outros"),
                params.get("forma_pagamento", "pix"),
                params.get("descricao", "Compra parcelada"),
                float(str(valor_total).replace(",", ".")),
                int(total_parcelas),
            )
            enviar_whatsapp(from_number, "✅ Compra parcelada registrada e planilha atualizada!")

        elif acao == "registrar":
            registrar_transacao(
                (params.get("tipo_conta") or "empresa").lower(),
                (params.get("tipo_movimento") or "saida").lower(),
                params.get("categoria", "outros"),
                params.get("forma_pagamento", "pix"),
                params.get("descricao", "Transação"),
                float(str(params.get("valor", 0)).replace(",", ".")),
            )
            enviar_whatsapp(from_number, "✅ Transação registrada e planilha atualizada!")

        elif acao == "erro":
            enviar_whatsapp(from_number, f"❌ {params.get('mensagem','Erro ao processar IA')}")

        else:
            

            enviar_whatsapp(
                from_number,
                "Não entendi. Exemplos:\n"
                "• Gastei 25,50 na farmácia no pix (pessoal)\n"
                "• Paguei 300 pra costureira no pix (empresa)\n"
                "• Comprei 1500 parcelado em 3x no Santander\n"
                "• saldo empresa\n"
                "• fatura empresa santander\n"
                "• aprender: costureira = empresa / mao_de_obra"
                
            )

    except Exception as e:
        log("ERRO no webhook:", str(e))
        traceback.print_exc()

    return {"status": "ok"}
