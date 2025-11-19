"""
Типы слайдов для презентаций.

Этот модуль определяет полиморфную иерархию слайдов с базовым классом
и специализированными подклассами для разных типов контента.
"""

from dataclasses import dataclass, field
from typing import List, Optional, ClassVar
from abc import ABC, abstractmethod


@dataclass
class BaseSlideConfig(ABC):
    """
    Базовый абстрактный класс для всех типов слайдов.

    Определяет общий интерфейс и поля, присутствующие во всех слайдах.
    Каждый конкретный тип слайда наследуется от этого класса и добавляет
    свои специфичные поля и валидацию.

    Attributes:
        layout_type: Тип макета размещения изображений (single_wide, two_stack и т.д.)
        title: Заголовок слайда (обязательное поле)
        notes_source: Источник заметок (путь к MD файлу или inline текст)
        images: Список путей к изображениям
        layout_name: Имя макета PowerPoint (может переопределять глобальное значение)

        SLIDE_TYPE: Уникальный идентификатор типа слайда (определяется в подклассах)

    Example:
        Этот класс абстрактный, используйте конкретные подклассы:
        >>> slide = ContentSlideConfig(
        ...     layout_type="single_wide",
        ...     title="Мой слайд",
        ...     notes_source="Текст заметок"
        ... )
    """

    # Общие поля для всех типов слайдов
    layout_type: str
    title: str
    notes_source: str = ""
    images: List[str] = field(default_factory=list)
    layout_name: Optional[str] = None

    # Метаданные типа (класс-уровень, переопределяются в подклассах)
    SLIDE_TYPE: ClassVar[str]

    def __post_init__(self):
        """
        Базовая валидация после инициализации.

        Проверяет обязательные поля и вызывает специфичную валидацию подкласса.

        Raises:
            ValueError: Если обязательные поля пусты
        """
        if not self.title:
            raise ValueError(f"{self.__class__.__name__}: title не может быть пустым")
        if not self.layout_type:
            raise ValueError(
                f"{self.__class__.__name__}: layout_type не может быть пустым"
            )

        # Вызов кастомной валидации для подклассов
        self.validate()

    @abstractmethod
    def validate(self):
        """
        Специфичная для типа валидация.

        Каждый подкласс должен реализовать свои правила валидации.
        Вызывается автоматически в __post_init__.

        Raises:
            ValueError: Если валидация не прошла
        """
        pass

    def to_dict(self) -> dict:
        """
        Сериализация слайда в словарь (для JSON).

        Returns:
            Словарь с полями слайда, включая slide_type
        """
        return {
            "slide_type": self.SLIDE_TYPE,
            "layout_type": self.layout_type,
            "title": self.title,
            "notes_source": self.notes_source,
            "images": self.images,
            "layout_name": self.layout_name,
        }


@dataclass
class ContentSlideConfig(BaseSlideConfig):
    """
    Обычный контентный слайд.

    Стандартный тип слайда для большинства презентаций.
    Поддерживает различные макеты размещения изображений без дополнительных
    специфичных полей.

    Attributes:
        Наследует все поля от BaseSlideConfig, без дополнений.

    Example:
        >>> slide = ContentSlideConfig(
        ...     layout_type="single_wide",
        ...     title="Введение в Python",
        ...     notes_source="notes/intro.md",
        ...     images=["screenshot1.png"]
        ... )
    """

    SLIDE_TYPE: ClassVar[str] = "content"

    def validate(self):
        """
        Валидация контентного слайда.

        Для обычного контента нет дополнительных требований сверх базовых.
        """
        pass  # Нет дополнительных требований


@dataclass
class YouTubeTitleSlideConfig(BaseSlideConfig):
    """
    Титульный слайд для YouTube видео.

    Специализированный тип слайда для создания обложек YouTube видео.
    Содержит дополнительные поля для подзаголовка и номера в серии.

    Attributes:
        subtitle: Подзаголовок (обязательное поле)
        series_number: Номер в серии (опциональное, например "Часть 3")

        Требования:
        - layout_name автоматически устанавливается в "TitleLayout"
        - Ровно одно изображение (квадратная обложка)
        - subtitle не может быть пустым

    Example:
        >>> slide = YouTubeTitleSlideConfig(
        ...     layout_type="title_youtube",
        ...     title="Основы Python",
        ...     subtitle="Полное руководство для начинающих",
        ...     series_number="Часть 1",
        ...     images=["cover_square.jpg"]
        ... )
        >>> slide.layout_name  # Автоматически = "TitleLayout"
    """

    SLIDE_TYPE: ClassVar[str] = "title_youtube"
    REQUIRED_LAYOUT_NAME: ClassVar[str] = "TitleLayout"

    # Специфичные поля для титульного слайда
    subtitle: str = ""
    series_number: Optional[str] = None

    def __post_init__(self):
        """
        Инициализация с автоматической настройкой layout_name.

        Если layout_name не указан, автоматически устанавливается в TitleLayout.
        """
        # Автоматически устанавливаем layout_name если не указан
        if not self.layout_name:
            self.layout_name = self.REQUIRED_LAYOUT_NAME

        # Вызов базовой валидации
        super().__post_init__()

    def validate(self):
        """
        Валидация титульного слайда.

        Проверяет:
        - subtitle обязателен и не пустой
        - Ровно 1 изображение
        - layout_name соответствует требуемому

        Raises:
            ValueError: Если какое-то из требований не выполнено
        """
        if not self.subtitle:
            raise ValueError(
                "YouTubeTitleSlideConfig: subtitle обязателен и не может быть пустым"
            )

        if not self.images or len(self.images) != 1:
            raise ValueError(
                f"YouTubeTitleSlideConfig: требуется ровно 1 изображение (квадратная обложка), "
                f"предоставлено: {len(self.images)}"
            )

        if self.layout_name != self.REQUIRED_LAYOUT_NAME:
            raise ValueError(
                f"YouTubeTitleSlideConfig: layout_name должен быть '{self.REQUIRED_LAYOUT_NAME}', "
                f"получено: '{self.layout_name}'"
            )

    def to_dict(self) -> dict:
        """
        Сериализация с дополнительными полями.

        Returns:
            Словарь с базовыми полями + subtitle и series_number
        """
        d = super().to_dict()
        d.update(
            {
                "subtitle": self.subtitle,
                "series_number": self.series_number,
            }
        )
        return d
