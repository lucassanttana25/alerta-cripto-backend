# routers/alertas.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List

from database import alertas_collection, dispositivos_collection
from models import AlertaCreate, Dispositivo, AlertaBase

# Importa a função de autenticação do outro roteador
from .auth import get_current_user

router = APIRouter(
    prefix="/alertas",
    tags=["Alertas"]
)

@router.post("/{tipo}", status_code=201)
async def criar_ou_atualizar_alerta(tipo: str, data: AlertaCreate, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    if tipo not in ["compra", "venda"]:
        raise HTTPException(status_code=400, detail="O tipo deve ser 'compra' ou 'venda'.")

    alertas_collection.update_one(
        {'user_email': user_email, 'tipo': tipo},
        {'$set': {'preco_alvo': data.preco_alvo, 'ativo': True, 'tipo': tipo, 'user_email': user_email}},
        upsert=True
    )
    return {"mensagem": f"Alerta de {tipo} definido para o usuário {user_email}."}

@router.get("", response_model=List[AlertaBase])
async def ler_alertas_do_usuario(current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    alertas_db = list(alertas_collection.find({'user_email': user_email}))
    # Converte ObjectId para string para validação do Pydantic
    for alerta in alertas_db:
        alerta['_id'] = str(alerta['_id'])
    return alertas_db

@router.delete("/{tipo}", status_code=200)
async def desativar_alerta(tipo: str, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    if tipo not in ["compra", "venda"]:
        raise HTTPException(status_code=400, detail="O tipo deve ser 'compra' ou 'venda'.")
    
    result = alertas_collection.update_one(
        {'user_email': user_email, 'tipo': tipo},
        {'$set': {'ativo': False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Alerta do tipo '{tipo}' não encontrado para este usuário.")
    
    return {"mensagem": f"Alerta de {tipo} foi desativado."}

@router.post("/registrar-dispositivo", status_code=201, tags=["Dispositivos"])
async def registrar_dispositivo(data: Dispositivo, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    dispositivos_collection.update_one(
        {'token': data.token},
        {'$set': {'token': data.token, 'user_email': user_email, 'registrado_em': datetime.utcnow()}},
        upsert=True
    )
    return {"mensagem": f"Dispositivo registrado para o usuário {user_email}."}