"""
Ядро бизнес-логики Auto-Slide.

Этот пакет содержит основные компоненты:
- Анализатор шаблонов
- Очиститель Markdown
- Процессор изображений
- Построитель презентаций
"""

from .markdown_cleaner import (
    clean_markdown_for_notes,
    clean_markdown_preserve_structure,
    validate_markdown,
)
from .image_processor import (
    calculate_smart_dimensions,
    get_image_info,
    validate_image,
)

__all__ = [
    "clean_markdown_for_notes",
    "clean_markdown_preserve_structure",
    "validate_markdown",
    "calculate_smart_dimensions",
    "get_image_info",
    "validate_image",
]
