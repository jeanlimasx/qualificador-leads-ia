import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

from segmentos import SEGMENTOS

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODELO = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
MODELO_RESERVA = os.getenv("GEMINI_MODEL_RESERVA", "gemini-flash-lite-latest")
ERROS_TEMPORARIOS = {429, 500, 503}

app = FastAPI(
    title="Qualificador de Leads com IA",
    description="Analisa a mensagem de um lead, extrai as informações importantes e classifica o potencial de compra, de acordo com o segmento.",
)

ORIGENS_PERMITIDAS = os.getenv("ORIGENS_PERMITIDAS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origem.strip() for origem in ORIGENS_PERMITIDAS],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

class MensagemLead(BaseModel):
    segmento: str = Field(examples=["imobiliario"])
    mensagem: str = Field(
        examples=[
            "Oi! Vi o anúncio do apartamento na Vila Mariana. Tenho uns 600 mil, "
            "vou usar FGTS e queria me mudar até o fim do ano. Dá pra visitar no sábado?"
        ]
    )


class Informacao(BaseModel):
    campo: str
    valor: str


class AnaliseLead(BaseModel):
    classificacao: str
    pontuacao: int
    informacoes: list[Informacao]
    faltando: list[str]
    resumo: str
    proxima_acao: str


def montar_instrucoes(segmento: dict) -> str:
    criterios = "\n".join(f"- {c}" for c in segmento["criterios"])
    return f"""Você é um SDR especialista no segmento: {segmento['nome']}.
Contexto do negócio: {segmento['contexto']}

Analise a mensagem do lead e avalie estes critérios:
{criterios}

Regras:
1. Use SOMENTE informações escritas na mensagem. Nunca invente dados.
2. Critérios não mencionados vão na lista "faltando".
3. "classificacao" deve ser exatamente "quente", "morno" ou "frio".
   Um lead é quente quando: {segmento['regra_quente']}.
4. "pontuacao" vai de 0 a 100.
5. "proxima_acao" é a melhor próxima mensagem ou ação do vendedor, em uma frase.
Responda em português."""


def chamar_ia(mensagem: str, instrucoes: str):
    config = types.GenerateContentConfig(
        system_instruction=instrucoes,
        response_mime_type="application/json",
        response_schema=AnaliseLead,
        temperature=0.2,
    )
    ultimo_erro = None
    for modelo in [MODELO, MODELO_RESERVA]:
        for tentativa in range(3):
            try:
                return client.models.generate_content(
                    model=modelo, contents=mensagem, config=config
                )
            except errors.APIError as erro:
                ultimo_erro = erro
                if erro.code not in ERROS_TEMPORARIOS:
                    raise
                time.sleep(2**tentativa)
    raise ultimo_erro


@app.get("/")
def status():
    return {"status": "online", "projeto": "Qualificador de Leads com IA"}


@app.get("/segmentos")
def listar_segmentos():
    return {chave: dados["nome"] for chave, dados in SEGMENTOS.items()}


@app.post("/qualificar", response_model=AnaliseLead)
def qualificar(lead: MensagemLead):
    segmento = SEGMENTOS.get(lead.segmento)
    if segmento is None:
        raise HTTPException(
            status_code=404,
            detail=f"Segmento '{lead.segmento}' não encontrado. Opções: {', '.join(SEGMENTOS)}",
        )

    try:
        resposta = chamar_ia(lead.mensagem, montar_instrucoes(segmento))
    except Exception as erro:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar a IA: {erro}")

    return resposta.parsed