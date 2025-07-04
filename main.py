# main.py (Versão Final com Cache e API do Mercado Bitcoin)

import os
import sys
import asyncio
import time
from pymongo import MongoClient
import requests

import firebase_admin
from firebase_admin import credentials, messaging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# --- Configurações ---
# ATUALIZADO: Usando a API do Mercado Bitcoin
API_URL = "https://api.mercadobitcoin.net/api/v4/tickers?symbols=BTC-BRL"
INTERVALO_MONITORAMENTO_SEGUNDOS = 180 # A cada 3 minutos
DB_NAME = "alerta_cripto_db"
ALERTAS_COLLECTION_NAME = "alertas"
DISPOSITIVOS_COLLECTION_NAME = "dispositivos"

# Cache em memória para o preço do Bitcoin
cache_preco = {
    "preco_brl": None,
    "timestamp": 0
}

# --- Inicialização dos Serviços ---
try:
    MONGO_URI = os.environ.get("MONGO_URI")
    if not MONGO_URI: raise ValueError("MONGO_URI não encontrado no .env")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    alertas_collection = db[ALERTAS_COLLECTION_NAME]
    dispositivos_collection = db[DISPOSITIVOS_COLLECTION_NAME]
    client.admin.command('ping')
    print("✔ Conexão com o MongoDB Atlas estabelecida!")

    FIREBASE_CREDENTIALS_PATH = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    if not FIREBASE_CREDENTIALS_PATH: raise ValueError("FIREBASE_CREDENTIALS_PATH não encontrado no .env")
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    print("✔ Conexão com o Firebase estabelecida!")
except Exception as e:
    print(f"ERRO CRÍTICO na inicialização: {e}")
    sys.exit(1)

# --- Modelos de Dados (Pydantic) ---
class AlertaBase(BaseModel): id: str = Field(..., alias='_id'); tipo: str; preco_alvo: float; ativo: bool
class AlertaCreate(BaseModel): preco_alvo: float
class Dispositivo(BaseModel): token: str

app = FastAPI(title="API de Alerta de Preço de Bitcoin", version="1.3.0")

# --- Lógica de Negócio e Tarefas ---

async def enviar_notificacao_push(token: str, titulo: str, corpo: str):
    try:
        message = messaging.Message(notification=messaging.Notification(title=titulo, body=corpo), token=token)
        messaging.send(message)
        print(f"INFO: Notificação enviada com sucesso para o token '{token[:20]}...'")
    except Exception as e:
        print(f"ERRO: Falha ao enviar notificação para o token '{token[:20]}...': {e}")

async def atualizar_preco_no_cache():
    """Função que busca o preço e o atualiza no nosso cache global usando a API do Mercado Bitcoin."""
    try:
        print("INFO: (Cache) Buscando novo preço na Mercado Bitcoin...")
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        
        if data and isinstance(data, list):
            cache_preco["preco_brl"] = float(data[0]['last'])
            cache_preco["timestamp"] = time.time()
            print(f"INFO: (Cache) Preço atualizado para R$ {cache_preco['preco_brl']:,.2f}")
        else:
            print("ERRO: (Cache) Resposta da API do MB em formato inesperado.")
    except Exception as e:
        print(f"ERRO: (Cache) Falha ao atualizar o preço do Mercado Bitcoin: {e}")

async def monitorar_alertas_e_precos():
    """Tarefa de fundo que atualiza o preço e verifica os alertas."""
    print("INFO: Tarefa de monitoramento e cache iniciada.")
    while True:
        await atualizar_preco_no_cache()

        preco_atual = cache_preco.get("preco_brl")
        if preco_atual is None:
            await asyncio.sleep(INTERVALO_MONITORAMENTO_SEGUNDOS)
            continue
        
        try:
            alertas_ativos = list(alertas_collection.find({'ativo': True}))
            print(f"INFO: Verificando {len(alertas_ativos)} alertas ativos com preço em cache de R$ {preco_atual:,.2f}")

            for alerta in alertas_ativos:
                alerta_atingido = False
                titulo, corpo = "", ""

                if alerta['tipo'] == 'compra' and preco_atual <= alerta['preco_alvo']:
                    titulo = "🎯 Alerta de Compra Atingido!"
                    corpo = f"Bitcoin (MB): R$ {preco_atual:,.2f}. Alvo de R$ {alerta['preco_alvo']:,.2f} atingido."
                    alerta_atingido = True
                
                if alerta['tipo'] == 'venda' and preco_atual >= alerta['preco_alvo']:
                    titulo = "💸 Alerta de Venda Atingido!"
                    corpo = f"Bitcoin (MB): R$ {preco_atual:,.2f}. Alvo de R$ {alerta['preco_alvo']:,.2f} atingido."
                    alerta_atingido = True
                
                if alerta_atingido:
                    print(f"INFO: {titulo}")
                    dispositivos = list(dispositivos_collection.find({}))
                    for dispositivo in dispositivos:
                        await enviar_notificacao_push(dispositivo['token'], titulo, corpo)
                    
                    alertas_collection.update_one({'_id': alerta['_id']}, {'$set': {'ativo': False}})
        except Exception as e:
            print(f"ERRO ao verificar alertas: {e}")
        
        await asyncio.sleep(INTERVALO_MONITORAMENTO_SEGUNDOS)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitorar_alertas_e_precos())

# --- Endpoints da API ---

@app.get("/", tags=["Status"])
def read_root():
    return {"status": "API de Alerta de Preços funcionando!", "fonte": "Mercado Bitcoin", "preco_em_cache": cache_preco}

@app.get("/preco-atual", tags=["Preço"])
def obter_preco_atual_do_cache():
    """Endpoint que retorna o preço atual que está em cache."""
    if cache_preco.get("preco_brl") is None:
        raise HTTPException(status_code=503, detail="O preço ainda não está disponível no cache.")
    # Este endpoint agora é usado apenas pelo app Android antigo.
    # A nova versão do app Android deve chamar um endpoint mais completo.
    return {"last": str(cache_preco["preco_brl"])}

@app.post("/alertas/{tipo}", status_code=201, tags=["Alertas"])
def criar_ou_atualizar_alerta(tipo: str, data: AlertaCreate):
    if tipo not in ["compra", "venda"]: raise HTTPException(status_code=400, detail="O tipo deve ser 'compra' ou 'venda'.")
    alertas_collection.update_one({'_id': f'alerta_{tipo}'}, {'$set': {'preco_alvo': data.preco_alvo, 'ativo': True, 'tipo': tipo}}, upsert=True)
    return {"mensagem": f"Alerta de {tipo} definido para R$ {data.preco_alvo:,.2f}."}

@app.get("/alertas", response_model=list[AlertaBase], tags=["Alertas"])
def ler_alertas(): return list(alertas_collection.find({}))

@app.delete("/alertas/{tipo}", status_code=200, tags=["Alertas"])
def desativar_alerta(tipo: str):
    if tipo not in ["compra", "venda"]: raise HTTPException(status_code=400, detail="O tipo deve ser 'compra' ou 'venda'.")
    result = alertas_collection.update_one({'_id': f'alerta_{tipo}'}, {'$set': {'ativo': False}})
    if result.matched_count == 0: raise HTTPException(status_code=404, detail=f"Alerta do tipo '{tipo}' não encontrado.")
    return {"mensagem": f"Alerta de {tipo} foi desativado."}

@app.post("/registrar-dispositivo", status_code=201, tags=["Dispositivos"])
def registrar_dispositivo(data: Dispositivo):
    dispositivos_collection.update_one({'token': data.token}, {'$set': {'token': data.token}}, upsert=True)
    return {"mensagem": "Dispositivo registrado com sucesso!"}