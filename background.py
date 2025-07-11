# background.py
import asyncio
import time
import requests
import firebase_admin
from firebase_admin import messaging

from database import alertas_collection, dispositivos_collection

# Configuração da API externa
API_URL = "https://api.mercadobitcoin.net/api/v4/tickers?symbols=BTC-BRL"
INTERVALO_MONITORAMENTO_SEGUNDOS = 180

cache_preco = {"preco_brl": None, "timestamp": 0}

async def enviar_notificacao_push(token: str, titulo: str, corpo: str):
    # (código inalterado)
    try:
        message = messaging.Message(notification=messaging.Notification(title=titulo, body=corpo), token=token)
        messaging.send(message)
        print(f"INFO: Notificação enviada com sucesso para o token '{token[:20]}...'")
    except Exception as e:
        print(f"ERRO: Falha ao enviar notificação para o token '{token[:20]}...': {e}")


async def atualizar_preco_no_cache():
    # (código inalterado)
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            cache_preco["preco_brl"] = float(data[0]['last'])
            cache_preco["timestamp"] = time.time()
            print(f"INFO: (Cache) Preço atualizado para R$ {cache_preco['preco_brl']:,.2f}")
    except Exception as e:
        print(f"ERRO CRÍTICO: (Cache) Exceção ao tentar atualizar o preço: {e}")


async def monitorar_alertas_e_precos():
    print("INFO: Tarefa de monitoramento iniciada.")
    while True:
        await atualizar_preco_no_cache()
        preco_atual = cache_preco.get("preco_brl")
        if preco_atual is None:
            await asyncio.sleep(INTERVALO_MONITORAMENTO_SEGUNDOS)
            continue
        
        try:
            alertas_ativos = list(alertas_collection.find({'ativo': True}))
            if alertas_ativos: # Só imprime se houver alertas para verificar
                 print(f"INFO: Verificando {len(alertas_ativos)} alertas ativos com preço em cache de R$ {preco_atual:,.2f}")

            for alerta in alertas_ativos:
                alerta_atingido = False
                # CORREÇÃO: Inicializamos as variáveis aqui
                titulo, corpo = "", ""

                # CORREÇÃO: Lógica que define o título e corpo foi re-adicionada
                if alerta['tipo'] == 'compra' and preco_atual <= alerta['preco_alvo']:
                    titulo = "🎯 Alerta de Compra Atingido!"
                    corpo = f"Bitcoin (MB): R$ {preco_atual:,.2f}. Alvo de R$ {alerta['preco_alvo']:,.2f} atingido."
                    alerta_atingido = True
                
                if alerta['tipo'] == 'venda' and preco_atual >= alerta['preco_alvo']:
                    titulo = "💸 Alerta de Venda Atingido!"
                    corpo = f"Bitcoin (MB): R$ {preco_atual:,.2f}. Alvo de R$ {alerta['preco_alvo']:,.2f} atingido."
                    alerta_atingido = True
                
                if alerta_atingido:
                    user_email_do_alerta = alerta["user_email"]
                    print(f"INFO: Alerta atingido para o usuário {user_email_do_alerta}")
                    
                    dispositivos_do_usuario = list(dispositivos_collection.find({'user_email': user_email_do_alerta}))
                    for dispositivo in dispositivos_do_usuario:
                        # Agora as variáveis 'titulo' e 'corpo' existirão aqui
                        await enviar_notificacao_push(dispositivo['token'], titulo, corpo)
                    
                    alertas_collection.update_one({'_id': alerta['_id']}, {'$set': {'ativo': False}})
        except Exception as e:
            print(f"ERRO ao verificar alertas: {e}")
        
        await asyncio.sleep(INTERVALO_MONITORAMENTO_SEGUNDOS)