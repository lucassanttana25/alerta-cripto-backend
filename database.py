import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

load_dotenv()

# --- Configurações ---
DB_NAME = "alerta_cripto_db"
USERS_COLLECTION_NAME = "users"
ALERTAS_COLLECTION_NAME = "alertas"
DISPOSITIVOS_COLLECTION_NAME = "dispositivos"

# --- Conexão com o MongoDB ---
try:
    MONGO_URI = os.environ.get("MONGO_URI")
    if not MONGO_URI:
        raise ValueError("MONGO_URI não encontrado no .env")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db[USERS_COLLECTION_NAME]
    alertas_collection = db[ALERTAS_COLLECTION_NAME]
    dispositivos_collection = db[DISPOSITIVOS_COLLECTION_NAME]
    client.admin.command('ping')
    print("✔ Conexão com o MongoDB Atlas estabelecida!")
except Exception as e:
    print(f"ERRO CRÍTICO (MongoDB): {e}")
    sys.exit(1)

# --- Inicialização do Firebase Admin ---
try:
    FIREBASE_CREDENTIALS_PATH = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    if not FIREBASE_CREDENTIALS_PATH:
        raise ValueError("FIREBASE_CREDENTIALS_PATH não encontrado no .env")
    
    # Verifica se o app do Firebase já não foi inicializado (evita erros no reload)
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        print("✔ Conexão com o Firebase estabelecida!")
    else:
        print("✔ Conexão com o Firebase já existia.")
except Exception as e:
    print(f"ERRO CRÍTICO (Firebase): {e}")
    sys.exit(1)