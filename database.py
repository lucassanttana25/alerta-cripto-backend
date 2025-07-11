# database.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "alerta_cripto_db"
USERS_COLLECTION_NAME = "users"
ALERTAS_COLLECTION_NAME = "alertas"
DISPOSITIVOS_COLLECTION_NAME = "dispositivos"

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI não encontrado no .env")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_collection = db[USERS_COLLECTION_NAME]
alertas_collection = db[ALERTAS_COLLECTION_NAME]
dispositivos_collection = db[DISPOSITIVOS_COLLECTION_NAME]

print("✔ Conexão com o MongoDB Atlas estabelecida!")