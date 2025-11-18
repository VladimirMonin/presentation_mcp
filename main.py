#!/usr/bin/env python3
"""
Auto-Slide: PowerPoint Automation Pipeline

Главная точка входа для CLI приложения.
Для получения помощи запустите: python main.py --help
"""

import sys


def main():
    """
    Главная функция CLI.

    TODO: Интеграция с cli.commands после реализации CLI модуля.
    """
    print("Auto-Slide: PowerPoint Automation Pipeline")
    print("=" * 50)
    print()
    print("Статус: В разработке (Этап 1 завершён)")
    print("Структура пакетов создана:")
    print("  ✓ config/")
    print("  ✓ core/")
    print("  ✓ models/")
    print("  ✓ io_handlers/")
    print("  ✓ cli/")
    print()
    print("Следующий шаг: Реализация моделей данных (Этап 2)")
    print()
    print("Для продолжения разработки см. doc/plan/refactor_plan.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
