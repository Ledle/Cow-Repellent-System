import logging
import sys

# logger.py
import logging
import sys


def setup_logging(
    level=logging.DEBUG,
    log_file=None,
):
    logger = logging.getLogger()
    logger.setLevel(level)

    # очищаем старые handlers
    logger.handlers.clear()

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")

    # терминал
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(level)

    logger.addHandler(console)

    # файл (если нужен)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)

        logger.addHandler(file_handler)
