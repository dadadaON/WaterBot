from pathlib import Path
from environs import Env
import logging

# Налаштування логування
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

env = Env()
env.read_env()

# Логуємо значення змінних
logger.debug("Loading configuration...")
BOT_TOKEN = env.str("BOT_TOKEN")
logger.debug(f"Loaded BOT_TOKEN: {BOT_TOKEN}")
ADMINS = env.list("ADMINS")

# ID групи для сповіщень
NOTIFICATION_GROUP_ID = -4755037492

# Шляхи до файлів Google API
BASE_DIR = Path(__file__).parent
GOOGLE_CREDENTIALS_FILE = BASE_DIR / "client_secret.json"
TOKEN_PICKLE_FILE = BASE_DIR / "token.pickle"

# Налаштування бази даних
DATABASE_URL = env.str("DATABASE_URL", default="sqlite+aiosqlite:///database.db")

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