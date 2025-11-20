"""
Модели данных Auto-Slide.

Этот пакет содержит dataclass-модели для:
- Конфигурации презентации
- Конфигурации слайдов (полиморфные типы)
- Реестра макетов
- Фабрики слайдов
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
from .slide_types import (
    BaseSlideConfig,
    ContentSlideConfig,
    YouTubeTitleSlideConfig,
)
from .slide_factory import SlideConfigFactory

__all__ = [
    # Старые классы (обратная совместимость)
    "SlideConfig",
    "PresentationConfig",
    "validate_config",
    # Макеты
    "ImagePlacement",
    "LayoutBlueprint",
    "LayoutRegistry",
    # Новые полиморфные типы слайдов
    "BaseSlideConfig",
    "ContentSlideConfig",
    "YouTubeTitleSlideConfig",
    "SlideConfigFactory",
]
