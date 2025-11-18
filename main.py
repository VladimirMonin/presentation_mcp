#!/usr/bin/env python3
"""
Auto-Slide: PowerPoint Automation Pipeline

Главная точка входа для CLI приложения.
Для получения помощи запустите: python main.py --help
"""

import sys
from cli import parse_args


def main():
    """
    Главная функция CLI.
    
    Парсит аргументы командной строки и выполняет соответствующую команду.
    """
    return parse_args(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())