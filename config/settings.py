"""
Настройки и константы по умолчанию для Auto-Slide.

Этот модуль содержит регистрацию стандартных макетов слайдов.
"""

from models import LayoutRegistry, LayoutBlueprint, ImagePlacement


def register_default_layouts(registry: LayoutRegistry) -> None:
    """
    Регистрирует стандартные макеты слайдов в реестре.

    Макеты соответствуют координатам из оригинального шаблона template.pptx.
    Все размеры указаны в сантиметрах.

    Args:
        registry: Реестр макетов для регистрации.

    Example:
        >>> registry = LayoutRegistry()
        >>> register_default_layouts(registry)
        >>> print(registry.list_all())
        ['single_wide', 'single_tall', 'two_stack', 'two_tall_row']
    """

    # Макет 1: Одно широкое изображение
    # Используется для горизонтальных скриншотов
    single_wide = LayoutBlueprint(
        name="single_wide",
        description="Одно широкое изображение (горизонтальное)",
        required_images=1,
        placements=[
            ImagePlacement(left=10.2, top=4.2, max_width=20.0, max_height=10.0)
        ],
    )
    registry.register(single_wide)

    # Макет 2: Одно высокое изображение
    # Используется для вертикальных скриншотов
    single_tall = LayoutBlueprint(
        name="single_tall",
        description="Одно высокое изображение (вертикальное)",
        required_images=1,
        placements=[
            ImagePlacement(left=10.46, top=2.96, max_width=11.2, max_height=15.2)
        ],
    )
    registry.register(single_tall)

    # Макет 3: Два изображения друг под другом (стек)
    # Используется для сравнения или последовательных скриншотов
    two_stack = LayoutBlueprint(
        name="two_stack",
        description="Два изображения друг под другом (вертикальный стек)",
        required_images=2,
        placements=[
            # Верхнее изображение
            ImagePlacement(left=10.16, top=3.47, max_width=18.4, max_height=3.91),
            # Нижнее изображение
            ImagePlacement(left=10.16, top=11.0, max_width=18.07, max_height=4.58),
        ],
    )
    registry.register(two_stack)

    # Макет 4: Два высоких изображения рядом (ряд)
    # Используется для сравнения вертикальных элементов
    two_tall_row = LayoutBlueprint(
        name="two_tall_row",
        description="Два высоких изображения рядом (горизонтальный ряд)",
        required_images=2,
        placements=[
            # Левое изображение
            ImagePlacement(left=10.2, top=2.4, max_width=10.5, max_height=14.5),
            # Правое изображение
            ImagePlacement(left=21.89, top=2.4, max_width=10.5, max_height=14.5),
        ],
    )
    registry.register(two_tall_row)

    # Макет 5: Три изображения друг под другом (вертикальный стек)
    # Используется для последовательного показа шагов или сравнения трёх элементов
    three_stack = LayoutBlueprint(
        name="three_stack",
        description="Три изображения друг под другом (вертикальный стек)",
        required_images=3,
        placements=[
            # Верхнее изображение
            ImagePlacement(left=10.16, top=3.0, max_width=18.4, max_height=4.0),
            # Среднее изображение
            ImagePlacement(left=10.16, top=7.5, max_width=18.4, max_height=4.0),
            # Нижнее изображение
            ImagePlacement(left=10.16, top=12.0, max_width=18.4, max_height=4.0),
        ],
    )
    registry.register(three_stack)

    # Макет 6: Титульный слайд YouTube
    # Используется для заглавного слайда видео с логотипом канала
    title_youtube = LayoutBlueprint(
        name="title_youtube",
        description="Титульный слайд YouTube (логотип в желтом квадрате справа)",
        required_images=1,
        placements=[
            # Логотип канала - точные координаты из PowerPoint
            # Позиция: 14.41 см от левого края, 0 см от верха
            # Размер: 19.46 x 19.05 см (с сохранением пропорций)
            ImagePlacement(left=14.41, top=0.0, max_width=19.46, max_height=19.05)
        ],
    )
    registry.register(title_youtube)


# Константы для работы с шаблоном
DEFAULT_TEMPLATE_PATH = "template.pptx"
DEFAULT_OUTPUT_PATH = "output.pptx"
DEFAULT_LAYOUT_NAME = "VideoLayout"

# ID заполнителей в шаблоне (из analyze_template.py)
PLACEHOLDER_TITLE_IDX = 10
PLACEHOLDER_SLIDE_NUM_IDX = 11
