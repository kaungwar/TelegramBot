import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration - Token is now only in .env
TOKEN = os.getenv("BOT_TOKEN")  # Required - no default value here

# Validate token exists
if not TOKEN:
    raise ValueError("No BOT_TOKEN found in .env file")

# File paths
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)

PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
TABLES_FILE = os.path.join(DATA_DIR, "tables.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")

# Conversation states
ADD_PRODUCT, ADD_TABLE, EDIT_PRODUCT, EDIT_TABLE, INPUT_QTY = range(5)
