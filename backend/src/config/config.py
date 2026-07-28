import os
from dotenv import load_dotenv

# Carga las variables del archivo .env al entorno del proceso
load_dotenv()

# TruckNet
TRUCKNET_USER = os.getenv("TRUCKNET_USER")
TRUCKNET_PASSWORD = os.getenv("TRUCKNET_PASSWORD")
TRUCKNET_LOGIN_URL = os.getenv("TRUCKNET_LOGIN_URL")
TRUCKNET_TRANS_URL = os.getenv("TRUCKNET_TRANS_URL")
TRUCKNET_TENANT = os.getenv("TRUCKNET_TENANT") or os.getenv("TRUCKNET_TENANT_ID")
TRUCKNET_ENV = (os.getenv("TRUCKNET_ENV") or "UAT").upper()

if not TRUCKNET_LOGIN_URL and TRUCKNET_TENANT:
    if TRUCKNET_ENV == "UAT":
        base = f"https://webuat.triniumtech.com/fpas/{TRUCKNET_TENANT}/web/api"
    else:
        base = f"https://web.triniumtech.com/fpas/{TRUCKNET_TENANT}/web/api"
    TRUCKNET_LOGIN_URL = f"{base}/login"
    if not TRUCKNET_TRANS_URL:
        TRUCKNET_TRANS_URL = f"{base}/transactions"

# XIGA
XIGA1_USER = os.getenv("XIGA1_USER")
XIGA1_PASSWORD = os.getenv("XIGA1_PASSWORD")
XIGA2_USER = os.getenv("XIGA2_USER")
XIGA2_PASSWORD = os.getenv("XIGA2_PASSWORD")
XIGA_LOGIN_URL = os.getenv("XIGA_LOGIN_URL")
XIGA_CONSUMPTIONS_URL = os.getenv("XIGA_CONSUMPTIONS_URL")

# Base de datos
DB_SERVER = os.getenv("DB_SERVER")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")