# main.py
import asyncio
from fastapi import FastAPI

# Importa os roteadores e a tarefa de background
from routers import auth, alertas
from background import monitorar_alertas_e_precos

# --- Inicialização da Aplicação ---
app = FastAPI(
    title="API de Alerta de Preço de Bitcoin",
    version="2.0.0 com Refatoração"
)

@app.on_event("startup")
async def startup_event():
    # Inicia a tarefa de monitoramento quando a API começa
    asyncio.create_task(monitorar_alertas_e_precos())

# --- Sincronização com os Roteadores ---
app.include_router(auth.router)
app.include_router(alertas.router)

# --- Endpoint Principal ---
@app.get("/", tags=["Status"])
def read_root():
    return {"status": "API de Alerta de Preços com autenticação está funcionando!"}