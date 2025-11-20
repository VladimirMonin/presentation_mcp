"""
Централизованная система логирования для Presentation Builder.

Настраивает три потока логов:
1. Console (stdout) - INFO или DEBUG с --verbose
2. logs/app.log - полная история (DEBUG)
3. logs/error.log - только ошибки (ERROR+)

Использует RotatingFileHandler для автоматической ротации файлов.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


class SafeConsoleHandler(logging.StreamHandler):
    """
    StreamHandler с защитой от UnicodeEncodeError в Windows console (cp1251).
    При ошибке кодировки заменяет символы на '?' вместо краша.
    """

    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            # Fallback: заменяем непечатаемые символы (эмодзи) на '?'
            try:
                msg = self.format(record)
                safe_msg = msg.encode(
                    self.stream.encoding or "utf-8", errors="replace"
                ).decode(self.stream.encoding or "utf-8")
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)


def setup_logging(verbose: bool = False, log_dir: str = "logs"):
    """
    Настраивает глобальный логгер приложения.

    Args:
        verbose: Если True, выводит DEBUG в консоль (по умолчанию только INFO)
        log_dir: Директория для файлов логов (по умолчанию "logs")

    Структура:
        - Console: INFO (или DEBUG при verbose)
        - logs/app.log: DEBUG (все детали + ротация 5MB × 3)
        - logs/error.log: ERROR (только ошибки + ротация 5MB × 3)
    """
    # 1. Создаем директорию для логов
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 2. Базовый форматтер
    # Пример: [2025-11-20 14:00:01] INFO     core.builder:45 - 🚀 Начало сборки
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-8s %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Упрощенный форматтер для консоли в обычном режиме
    console_formatter_simple = logging.Formatter("%(levelname)-8s %(message)s")

    # 3. Получаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Ловим всё, фильтруем на хендлерах

    # Очищаем существующие хендлеры (чтобы не дублировались при перезапуске)
    root_logger.handlers.clear()

    # --- HANDLER 1: CONSOLE (с защитой от emoji в Windows) ---
    console_handler = SafeConsoleHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # В verbose режиме показываем полный формат, иначе упрощенный
    if verbose:
        console_handler.setFormatter(formatter)
    else:
        console_handler.setFormatter(console_formatter_simple)

    root_logger.addHandler(console_handler)

    # --- HANDLER 2: APP.LOG (Full Debug) ---
    # RotatingFileHandler не даст файлу разрастись до гигабайт
    # 5 МБ на файл, храним 3 последних архива
    app_log_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    app_log_handler.setLevel(logging.DEBUG)
    app_log_handler.setFormatter(formatter)
    root_logger.addHandler(app_log_handler)

    # --- HANDLER 3: ERROR.LOG (Errors Only) ---
    error_log_handler = RotatingFileHandler(
        log_path / "error.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    error_log_handler.setLevel(logging.ERROR)
    error_log_handler.setFormatter(formatter)
    root_logger.addHandler(error_log_handler)

    # Сообщение о том, что логирование инициализировано
    logging.info("⚙️ Система логирования инициализирована")
    logging.debug(f"📂 Логи сохраняются в: {log_path.resolve()}")
