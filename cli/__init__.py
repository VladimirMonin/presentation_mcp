"""
Интерфейс командной строки Auto-Slide.

Этот пакет содержит CLI команды для:
- Генерации презентаций (generate)
- Анализа шаблонов (analyze)
"""

from .commands import (
    cmd_generate,
    cmd_analyze,
    cmd_help,
    parse_args,
)

__all__ = [
    'cmd_generate',
    'cmd_analyze',
    'cmd_help',
    'parse_args',
]
