# main.py (Versão Corrigida com todos os endpoints)
import asyncio
from fastapi import FastAPI, HTTPException

# Importa os roteadores e as funções/variáveis necessárias dos outros arquivos
from routers import auth, alertas
from background import monitorar_alertas_e_precos, atualizar_preco_no_cache, cache_preco

# --- Inicialização da Aplicação ---
app = FastAPI(
    title="API de Alerta de Preço de Bitcoin",
    version="2.1.0 - Refatoração Completa"
)

@app.on_event("startup")
async def startup_event():
    # Inicia a tarefa de monitoramento quando a API começa
    print("INFO: Iniciando tarefa de monitoramento em background...")
    asyncio.create_task(monitorar_alertas_e_precos())

# --- Sincronização com os Roteadores ---
app.include_router(auth.router)
app.include_router(alertas.router)

# --- Endpoints Públicos ---

@app.get("/", tags=["Status"])
def read_root():
    """Endpoint raiz para verificar se a API está online."""
    return {"status": "API de Alerta de Preços com autenticação está funcionando!"}

@app.get("/preco-atual", tags=["Preço"])
async def obter_preco_atual():
    """
    Endpoint público que retorna o preço do cache.
    Força uma atualização se o cache estiver vazio (na primeira chamada).
    """
    # Se o cache estiver vazio, força uma atualização para garantir que o app sempre tenha um preço na primeira vez.
    if cache_preco.get("preco_brl") is None:
        print("INFO: Cache vazio no endpoint /preco-atual. Forçando atualização...")
        await atualizar_preco_no_cache()

    preco_final = cache_preco.get("preco_brl")
    if preco_final is None:
        # Se mesmo após a tentativa o cache ainda estiver vazio, retorna um erro.
        raise HTTPException(status_code=503, detail="Não foi possível obter o preço da API externa no momento.")

    # Retorna o preço no formato que o app Android espera
    return {"bitcoin": {"brl": preco_final}}