#!/usr/bin/env python3
"""
Auto-Slide: PowerPoint Automation Pipeline

Главная точка входа для CLI приложения.
Для получения помощи запустите: python main.py --help
"""

import sys
import logging
from cli import parse_args
from core import setup_logging


def main():
    """
    Главная функция CLI.

    Парсит аргументы командной строки и выполняет соответствующую команду.
    """
    # Определяем verbose режим из аргументов до парсинга
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    # Инициализируем систему логирования
    setup_logging(verbose=verbose)

    logger = logging.getLogger(__name__)
    logger.debug(f"🚀 Приложение запущено с аргументами: {sys.argv}")

    try:
        return parse_args(sys.argv[1:])
    except Exception as e:
        logger.critical(
            f"💥 Необработанное исключение на верхнем уровне: {e}", exc_info=True
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
