# logger.py
import logging
from logging.handlers import RotatingFileHandler
import os

# Diretório para logs (opcional)
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Caminho do arquivo de log
LOG_FILE = os.path.join(LOG_DIR, "processador.log")

# Configuração básica
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # ou INFO, WARNING...

# Evita handlers duplicados quando importar várias vezes
if not logger.handlers:
    # Formato
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s - %(lineno)d:"
    )

    # Handler para arquivo (com rotação)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=5)
    file_handler.setFormatter(formatter)

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
