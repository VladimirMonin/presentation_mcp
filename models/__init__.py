"""
Модели данных Auto-Slide.

Этот пакет содержит dataclass-модели для:
- Конфигурации презентации
- Конфигурации слайдов
- Реестра макетов
"""

from .config_schema import (
    SlideConfig,
    PresentationConfig,
    validate_config,
)
from .layout_registry import (
    ImagePlacement,
    LayoutBlueprint,
    LayoutRegistry,
)

__all__ = [
    "SlideConfig",
    "PresentationConfig",
    "validate_config",
    "ImagePlacement",
    "LayoutBlueprint",
    "LayoutRegistry",
]
