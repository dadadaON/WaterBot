from pathlib import Path
from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS")

# Шляхи до файлів Google API
BASE_DIR = Path(__file__).parent
GOOGLE_CREDENTIALS_FILE = BASE_DIR / "client_secret.json"
TOKEN_PICKLE_FILE = BASE_DIR / "token.pickle"

# Налаштування бази даних
DATABASE_URL = env.str("DATABASE_URL", default="sqlite+aiosqlite:///bot.db")

# Налаштування безпеки
WEBHOOK_HOST = env.str("WEBHOOK_HOST", default=None)
WEBHOOK_PATH = env.str("WEBHOOK_PATH", default=None)
WEBAPP_HOST = env.str("WEBAPP_HOST", default="0.0.0.0")
WEBAPP_PORT = env.int("WEBAPP_PORT", default=3000)

# Налаштування Google API
GOOGLE_API_SCOPES = [
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/tasks.readonly'
] 