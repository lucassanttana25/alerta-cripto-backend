# routers/auth.py

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

# CORREÇÃO: Importando TODAS as coleções que vamos usar neste arquivo
from database import users_collection, dispositivos_collection
from models import Token, UserCreate, UserLogin

# --- Configurações de Segurança ---
SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key_for_development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 dias

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

# --- Funções Auxiliares ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependência para Obter Usuário Atual ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = users_collection.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return user

# --- Endpoints ---
@router.post("/register")
async def register_user(data: UserCreate):
    user_in_db = users_collection.find_one({"email": data.email})
    if user_in_db:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    hashed_password = get_password_hash(data.password)
    new_user = {"email": data.email, "hashed_password": hashed_password}
    users_collection.insert_one(new_user)
    
    # Registra o dispositivo e o associa ao email do novo usuário
    if data.token:
        dispositivos_collection.update_one(
            {'token': data.token},
            {'$set': {'token': data.token, 'user_email': data.email, 'registrado_em': datetime.utcnow()}},
            upsert=True
        )
        
    return {"message": "Usuário criado e dispositivo associado com sucesso"}

@router.post("/login", response_model=Token)
async def login_for_access_token(data: UserLogin): # Usa o novo modelo UserLogin
    user = users_collection.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}