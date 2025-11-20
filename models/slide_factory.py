"""
Фабрика для создания слайдов из JSON данных.

Автоматически выбирает правильный класс слайда на основе поля slide_type.
"""

from typing import Dict, Any, Type
from .slide_types import (
    BaseSlideConfig,
    ContentSlideConfig,
    YouTubeTitleSlideConfig,
)


class SlideConfigFactory:
    """
    Фабрика для создания правильного типа SlideConfig из JSON данных.

    Автоматически выбирает класс на основе поля 'slide_type' в JSON.
    Поддерживает регистрацию новых типов слайдов без изменения кода фабрики.

    Attributes:
        _registry: Словарь типов слайдов {slide_type: SlideConfigClass}

    Example:
        >>> factory = SlideConfigFactory()
        >>> data = {
        ...     "slide_type": "content",
        ...     "layout_type": "single_wide",
        ...     "title": "Слайд",
        ...     "notes_source": "Заметки"
        ... }
        >>> slide = factory.create(data)
        >>> isinstance(slide, ContentSlideConfig)
        True
    """

    # Реестр типов слайдов
    _registry: Dict[str, Type[BaseSlideConfig]] = {
        "content": ContentSlideConfig,
        "title_youtube": YouTubeTitleSlideConfig,
    }

    @classmethod
    def create(cls, data: Dict[str, Any]) -> BaseSlideConfig:
        """
        Создает экземпляр SlideConfig из словаря.

        Args:
            data: Словарь с данными слайда (из JSON)

        Returns:
            Экземпляр соответствующего подкласса BaseSlideConfig

        Raises:
            ValueError: Если slide_type неизвестен

        Example:
            >>> data = {"slide_type": "title_youtube", "title": "Заголовок", ...}
            >>> slide = SlideConfigFactory.create(data)
            >>> isinstance(slide, YouTubeTitleSlideConfig)
            True
        """
        slide_type = data.get("slide_type")

        # Fallback: если slide_type не указан, считаем обычным контентом
        if not slide_type:
            slide_type = "content"

        if slide_type not in cls._registry:
            raise ValueError(
                f"Неизвестный slide_type: '{slide_type}'. "
                f"Доступные типы: {list(cls._registry.keys())}"
            )

        slide_class = cls._registry[slide_type]

        # Удаляем slide_type из данных (его нет в полях класса)
        data_copy = data.copy()
        data_copy.pop("slide_type", None)

        try:
            return slide_class(**data_copy)
        except TypeError as e:
            raise ValueError(
                f"Ошибка создания слайда типа '{slide_type}': {e}. "
                f"Проверьте соответствие полей в JSON."
            ) from e

    @classmethod
    def register(cls, slide_type: str, slide_class: Type[BaseSlideConfig]):
        """
        Регистрирует новый тип слайда.

        Позволяет добавлять кастомные типы без изменения фабрики.

        Args:
            slide_type: Уникальный идентификатор типа
            slide_class: Класс слайда (подкласс BaseSlideConfig)

        Raises:
            ValueError: Если тип уже зарегистрирован

        Example:
            >>> class CustomSlideConfig(BaseSlideConfig):
            ...     SLIDE_TYPE = "custom"
            ...     def validate(self): pass
            >>> SlideConfigFactory.register("custom", CustomSlideConfig)
        """
        if slide_type in cls._registry:
            raise ValueError(
                f"slide_type '{slide_type}' уже зарегистрирован. "
                f"Используйте другое имя или удалите существующую регистрацию."
            )
        cls._registry[slide_type] = slide_class

    @classmethod
    def get_registered_types(cls) -> list:
        """
        Возвращает список всех зарегистрированных типов слайдов.

        Returns:
            Список строк с именами типов

        Example:
            >>> SlideConfigFactory.get_registered_types()
            ['content', 'title_youtube']
        """
        return list(cls._registry.keys())
