# models.py
from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str
    token_type: str

class AlertaBase(BaseModel):
    id: str = Field(alias='_id') # Usamos alias para o campo _id do MongoDB
    tipo: str
    preco_alvo: float
    ativo: bool
    user_email: str

class AlertaCreate(BaseModel):
    preco_alvo: float

class Dispositivo(BaseModel):
    token: str

class User(BaseModel):
    email: str

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    email: str
    password: str
    token: str # O token do dispositivo FCM

class UserLogin(BaseModel):
    email: str
    password: str