"""
Модели данных для конфигурации презентаций.

Этот модуль определяет структуру JSON конфигураций и обеспечивает
типобезопасность при работе с данными презентации.
"""

from dataclasses import dataclass, field
from typing import List


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

    Example:
        >>> slide = SlideConfig(
        ...     layout_type="single_wide",
        ...     title="Введение",
        ...     notes_source="notes/intro.md",
        ...     images=["images/diagram.png"]
        ... )
    """

    layout_type: str
    title: str
    notes_source: str
    images: List[str] = field(default_factory=list)

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
        template_path: Путь к файлу шаблона .pptx (может быть относительным или абсолютным).
                       По умолчанию: "template.pptx".
        output_path: Путь для сохранения итоговой презентации.
                     По умолчанию: "output.pptx".
        layout_name: Имя макета в шаблоне PPTX (используется для поиска слайд-макета).
                     По умолчанию: "VideoLayout".

    Example JSON:
        {
            "template_path": "template.pptx",
            "output_path": "my_presentation.pptx",
            "layout_name": "VideoLayout",
            "slides": [
                {
                    "layout_type": "single_wide",
                    "title": "Заголовок",
                    "notes_source": "notes/slide1.md",
                    "images": ["images/pic1.png"]
                }
            ]
        }

    Example:
        >>> config = PresentationConfig(
        ...     template_path="custom_template.pptx",
        ...     output_path="result.pptx",
        ...     slides=[slide1, slide2]
        ... )
    """

    slides: List[SlideConfig]
    template_path: str = "template.pptx"
    output_path: str = "output.pptx"
    layout_name: str = "VideoLayout"

    def __post_init__(self):
        """Валидация после инициализации."""
        if not self.slides:
            raise ValueError("slides не может быть пустым списком")

        # Конвертируем словари в SlideConfig если нужно
        self.slides = [
            SlideConfig(**s) if isinstance(s, dict) else s for s in self.slides
        ]


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
