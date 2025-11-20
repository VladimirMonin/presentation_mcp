"""
Модели данных для конфигурации презентаций.

Этот модуль определяет структуру JSON конфигураций и обеспечивает
типобезопасность при работе с данными презентации.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from models.slide_types import BaseSlideConfig
from models.slide_factory import SlideConfigFactory


@dataclass
class SlideConfig:
    """
    Конфигурация одного слайда презентации.

    Attributes:
        layout_type: Тип макета слайда (например, 'single_wide', 'two_stack').
                     Должен соответствовать зарегистрированному макету в LayoutRegistry.
        title: Заголовок слайда (обязательное поле).
        notes_source: Источник текста заметок докладчика. Может быть:
                      - Путь к .md файлу (относительный или абсолютный)
                      - Inline текст в формате Markdown
                      Текст будет очищен от Markdown разметки перед добавлением в заметки.
        images: Список путей к изображениям для размещения на слайде.
                Пути могут быть относительными (относительно JSON) или абсолютными.
                Количество изображений должно соответствовать требованиям макета.
        layout_name: Опциональное имя макета в PPTX шаблоне для этого конкретного слайда.
                     Если указано, переопределяет глобальное значение layout_name из PresentationConfig.
                     Это позволяет использовать разные макеты PowerPoint в одной презентации
                     (например, титульный слайд + контентные слайды).

    Example:
        >>> slide = SlideConfig(
        ...     layout_type="single_wide",
        ...     title="Введение",
        ...     notes_source="notes/intro.md",
        ...     images=["images/diagram.png"],
        ...     layout_name="ContentLayout"  # Переопределить для этого слайда
        ... )
    """

    layout_type: str
    title: str
    notes_source: str
    images: List[str] = field(default_factory=list)
    layout_name: Optional[str] = None

    def __post_init__(self):
        """Валидация после инициализации."""
        if not self.layout_type:
            raise ValueError("layout_type не может быть пустым")
        if not self.title:
            raise ValueError("title не может быть пустым")
        if not self.notes_source:
            raise ValueError("notes_source не может быть пустым")


@dataclass
class PresentationConfig:
    """
    Корневая конфигурация презентации.

    Attributes:
        slides: Список конфигураций слайдов (обязательное поле).
                Может содержать как SlideConfig (для обратной совместимости),
                так и BaseSlideConfig (ContentSlideConfig, YouTubeTitleSlideConfig и др.).
        template_path: Путь к файлу шаблона .pptx (может быть относительным или абсолютным).
                       По умолчанию: "template.pptx".
        output_path: Путь для сохранения итоговой презентации.
                     По умолчанию: "output.pptx".
        layout_name: Имя макета в шаблоне PPTX (используется для поиска слайд-макета).
                     По умолчанию: "VideoLayout".

    Example JSON:
        {
            "template_path": "templates/youtube_base.pptx",
            "output_path": "my_presentation.pptx",
            "layout_name": "VideoLayout",
            "slides": [
                {
                    "slide_type": "content",
                    "layout_type": "single_wide",
                    "title": "Заголовок",
                    "notes_source": "notes/slide1.md",
                    "images": ["images/pic1.png"]
                },
                {
                    "slide_type": "title_youtube",
                    "title": "Мой канал",
                    "subtitle": "Серия видео о Python",
                    "series_number": "Часть 1",
                    "notes_source": "notes/intro.md",
                    "images": ["images/logo.png"]
                }
            ]
        }

    Example:
        >>> config = PresentationConfig(
        ...     template_path="templates/youtube_base.pptx",
        ...     output_path="result.pptx",
        ...     slides=[slide1, slide2]
        ... )
    """

    slides: List[BaseSlideConfig]
    template_path: str = "template.pptx"
    output_path: str = "output.pptx"
    layout_name: str = "VideoLayout"

    def __post_init__(self):
        """Валидация после инициализации."""
        if not self.slides:
            raise ValueError("slides не может быть пустым списком")

        # Конвертируем словари в BaseSlideConfig через фабрику если нужно
        converted_slides = []
        for s in self.slides:
            if isinstance(s, dict):
                # Используем фабрику для создания правильного типа слайда
                converted_slides.append(SlideConfigFactory.create(s))
            elif isinstance(s, SlideConfig):
                # Конвертируем старый SlideConfig в ContentSlideConfig для обратной совместимости
                from models.slide_types import ContentSlideConfig

                converted_slides.append(
                    ContentSlideConfig(
                        layout_type=s.layout_type,
                        title=s.title,
                        notes_source=s.notes_source,
                        images=s.images,
                        layout_name=s.layout_name,
                    )
                )
            else:
                # Уже BaseSlideConfig или его подкласс
                converted_slides.append(s)

        self.slides = converted_slides


# Вспомогательные функции для работы с конфигурацией


def validate_config(config: PresentationConfig) -> List[str]:
    """
    Валидирует конфигурацию и возвращает список предупреждений.

    Args:
        config: Конфигурация для валидации.

    Returns:
        Список строк с предупреждениями (пустой список, если всё ОК).

    Example:
        >>> warnings = validate_config(config)
        >>> if warnings:
        ...     for warning in warnings:
        ...         print(f"WARNING: {warning}")
    """
    warnings = []

    # Проверка уникальности заголовков
    titles = [slide.title for slide in config.slides]
    duplicates = [title for title in set(titles) if titles.count(title) > 1]
    if duplicates:
        warnings.append(f"Обнаружены дублирующиеся заголовки: {', '.join(duplicates)}")

    # Проверка наличия изображений
    for i, slide in enumerate(config.slides, 1):
        if not slide.images:
            warnings.append(f"Слайд #{i} ('{slide.title}') не содержит изображений")

    return warnings
