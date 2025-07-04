# main.py (versão com Firebase)

import os
import sys
import asyncio
from pymongo import MongoClient
import requests # Movido para o topo para clareza
from datetime import datetime

# --- Novas Importações do Firebase ---
import firebase_admin
from firebase_admin import credentials, messaging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# --- Configurações ---
API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=brl"
INTERVALO_MONITORAMENTO_SEGUNDOS = 60
DB_NAME = "alerta_cripto_db"
# NOVAS COLEÇÕES
ALERTAS_COLLECTION_NAME = "alertas"
DISPOSITIVOS_COLLECTION_NAME = "dispositivos"

# --- Inicialização dos Serviços ---
# Conexão com MongoDB
try:
    MONGO_URI = os.environ.get("MONGO_URI")
    if not MONGO_URI: raise ValueError("MONGO_URI não encontrado no .env")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    alertas_collection = db[ALERTAS_COLLECTION_NAME]
    dispositivos_collection = db[DISPOSITIVOS_COLLECTION_NAME] # Nova coleção
    client.admin.command('ping')
    print("✔ Conexão com o MongoDB Atlas estabelecida!")
except Exception as e:
    print(f"ERRO CRÍTICO (MongoDB): {e}")
    sys.exit(1)

# NOVO: Inicialização do Firebase Admin
try:
    FIREBASE_CREDENTIALS_PATH = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    if not FIREBASE_CREDENTIALS_PATH: raise ValueError("FIREBASE_CREDENTIALS_PATH não encontrado no .env")
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    print("✔ Conexão com o Firebase estabelecida!")
except Exception as e:
    print(f"ERRO CRÍTICO (Firebase): {e}")
    sys.exit(1)

# --- Modelos de Dados (Pydantic) ---
class AlertaBase(BaseModel): id: str = Field(..., alias='_id'); tipo: str; preco_alvo: float; ativo: bool
class AlertaCreate(BaseModel): preco_alvo: float
# NOVO: Modelo para registrar um dispositivo
class Dispositivo(BaseModel): token: str

app = FastAPI(title="API de Alerta de Preço de Bitcoin", version="1.1.0")

# --- Lógica de Negócio ---
# Função auxiliar para buscar o preço na API da CoinGecko
def get_bitcoin_price():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException:
        return None
    
async def enviar_notificacao_push(token: str, titulo: str, corpo: str):
    """Envia uma notificação push para um token de dispositivo específico."""
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=titulo, body=corpo),
            token=token,
        )
        response = messaging.send(message)
        print(f"INFO:     Notificação enviada com sucesso para o token '{token[:20]}...': {response}")
    except Exception as e:
        print(f"ERRO:     Falha ao enviar notificação para o token '{token[:20]}...': {e}")
        # Se o token for inválido, podemos removê-lo do banco
        if isinstance(e, firebase_admin.exceptions.NotFoundError):
            dispositivos_collection.delete_one({"token": token})
            print(f"INFO:     Token inválido removido do banco de dados.")

async def monitorar_precos():
    print("INFO:     Tarefa de monitoramento iniciada.")
    while True:
        try:
            alertas_ativos = list(alertas_collection.find({'ativo': True}))
            if not alertas_ativos:
                await asyncio.sleep(INTERVALO_MONITORAMENTO_SEGUNDOS)
                continue

            response = requests.get(API_URL)
            response.raise_for_status()
            preco_atual = response.json()['bitcoin']['brl']
            print(f"INFO:     Preço BTC: R$ {preco_atual:,.2f} | Alertas: {len(alertas_ativos)}")

            for alerta in alertas_ativos:
                alerta_atingido = False
                titulo, corpo = "", ""

                if alerta['tipo'] == 'compra' and preco_atual <= alerta['preco_alvo']:
                    titulo = "🎯 Alerta de Compra Atingido!"
                    corpo = f"Bitcoin atingiu seu alvo de R$ {alerta['preco_alvo']:,.2f}. Preço atual: R$ {preco_atual:,.2f}"
                    alerta_atingido = True

                if alerta['tipo'] == 'venda' and preco_atual >= alerta['preco_alvo']:
                    titulo = "💸 Alerta de Venda Atingido!"
                    corpo = f"Bitcoin atingiu seu alvo de R$ {alerta['preco_alvo']:,.2f}. Preço atual: R$ {preco_atual:,.2f}"
                    alerta_atingido = True

                if alerta_atingido:
                    print(f"INFO:     {titulo}")
                    # MODIFICADO: Envia notificação para TODOS os dispositivos registrados
                    dispositivos = list(dispositivos_collection.find({}))
                    for dispositivo in dispositivos:
                        await enviar_notificacao_push(dispositivo['token'], titulo, corpo)

                    alertas_collection.update_one({'_id': alerta['_id']}, {'$set': {'ativo': False}})

        except Exception as e:
            print(f"ERRO na tarefa de monitoramento: {e}")

        await asyncio.sleep(INTERVALO_MONITORAMENTO_SEGUNDOS)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitorar_precos())

# --- Endpoints da API ---
@app.get("/", tags=["Status"])
def read_root(): return {"status": "API de Alerta de Preços funcionando!"}

@app.post("/alertas/{tipo}", status_code=201, tags=["Alertas"])
def criar_ou_atualizar_alerta(tipo: str, data: AlertaCreate):
    # (código do endpoint inalterado)
    if tipo not in ["compra", "venda"]: raise HTTPException(status_code=400, detail="O tipo deve ser 'compra' ou 'venda'.")
    alertas_collection.update_one({'_id': f'alerta_{tipo}'}, {'$set': {'preco_alvo': data.preco_alvo, 'ativo': True, 'tipo': tipo}}, upsert=True)
    return {"mensagem": f"Alerta de {tipo} definido para R$ {data.preco_alvo:,.2f}."}

@app.get("/alertas", response_model=list[AlertaBase], tags=["Alertas"])
def ler_alertas(): return list(alertas_collection.find({}))

@app.delete("/alertas/{tipo}", status_code=200, tags=["Alertas"])
def desativar_alerta(tipo: str):
    # (código do endpoint inalterado)
    if tipo not in ["compra", "venda"]: raise HTTPException(status_code=400, detail="O tipo deve ser 'compra' ou 'venda'.")
    result = alertas_collection.update_one({'_id': f'alerta_{tipo}'}, {'$set': {'ativo': False}})
    if result.matched_count == 0: raise HTTPException(status_code=404, detail=f"Alerta do tipo '{tipo}' não encontrado.")
    return {"mensagem": f"Alerta de {tipo} foi desativado."}

# NOVO ENDPOINT para simular o registro de um celular
@app.post("/registrar-dispositivo", status_code=201, tags=["Dispositivos"])
def registrar_dispositivo(data: Dispositivo):
    """Registra o token de um dispositivo para receber notificações."""
    # O upsert=True garante que não teremos tokens duplicados
    dispositivos_collection.update_one(
        {'token': data.token},
        {'$set': {'token': data.token, 'registrado_em': datetime.utcnow()}},
        upsert=True
    )
    return {"mensagem": "Dispositivo registrado com sucesso!"}

@app.get("/preco-atual", tags=["Preço"])
def obter_preco_atual():
    """Endpoint para obter o preço atual do Bitcoin da CoinGecko."""
    preco_data = get_bitcoin_price()
    if not preco_data:
        raise HTTPException(status_code=503, detail="Não foi possível obter o preço da API externa.")
    return preco_data