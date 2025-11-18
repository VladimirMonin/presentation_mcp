"""
Конфигурация проекта Auto-Slide.

Этот пакет содержит настройки по умолчанию, константы и регистрацию макетов.
"""

from .settings import (
    register_default_layouts,
    DEFAULT_TEMPLATE_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_LAYOUT_NAME,
    PLACEHOLDER_TITLE_IDX,
    PLACEHOLDER_SLIDE_NUM_IDX,
)

__all__ = [
    'register_default_layouts',
    'DEFAULT_TEMPLATE_PATH',
    'DEFAULT_OUTPUT_PATH',
    'DEFAULT_LAYOUT_NAME',
    'PLACEHOLDER_TITLE_IDX',
    'PLACEHOLDER_SLIDE_NUM_IDX',
]
