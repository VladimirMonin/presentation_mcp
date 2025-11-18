"""
Примеры использования моделей данных.

Этот скрипт демонстрирует создание и валидацию конфигураций.
Запустите: python -m models.examples
"""

from models import (
    SlideConfig,
    PresentationConfig,
    validate_config,
    ImagePlacement,
    LayoutBlueprint,
    LayoutRegistry,
)


def example_slide_config():
    """Пример создания конфигурации слайда."""
    print("=" * 60)
    print("Пример 1: Создание конфигурации слайда")
    print("=" * 60)

    slide = SlideConfig(
        layout_type="single_wide",
        title="Введение в Python",
        notes_source="notes/intro.md",
        images=["images/python_logo.png"],
    )

    print(f"Layout: {slide.layout_type}")
    print(f"Title: {slide.title}")
    print(f"Notes: {slide.notes_source}")
    print(f"Images: {slide.images}")
    print()


def example_presentation_config():
    """Пример создания конфигурации презентации."""
    print("=" * 60)
    print("Пример 2: Создание конфигурации презентации")
    print("=" * 60)

    config = PresentationConfig(
        template_path="template.pptx",
        output_path="my_presentation.pptx",
        slides=[
            SlideConfig(
                layout_type="single_wide",
                title="Слайд 1",
                notes_source="Заметки для первого слайда",
                images=["img1.png"],
            ),
            SlideConfig(
                layout_type="two_stack",
                title="Слайд 2",
                notes_source="notes/slide2.md",
                images=["img2.png", "img3.png"],
            ),
        ],
    )

    print(f"Template: {config.template_path}")
    print(f"Output: {config.output_path}")
    print(f"Slides count: {len(config.slides)}")

    # Валидация
    warnings = validate_config(config)
    if warnings:
        print("\nПредупреждения:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\n✓ Конфигурация валидна")
    print()


def example_layout_registry():
    """Пример работы с реестром макетов."""
    print("=" * 60)
    print("Пример 3: Реестр макетов")
    print("=" * 60)

    registry = LayoutRegistry()

    # Регистрация макета "single_wide"
    single_wide = LayoutBlueprint(
        name="single_wide",
        description="Одно широкое изображение",
        required_images=1,
        placements=[
            ImagePlacement(left=10.2, top=4.2, max_width=20.0, max_height=10.0)
        ],
    )
    registry.register(single_wide)
    print(f"✓ Зарегистрирован макет: {single_wide.name}")

    # Регистрация макета "two_stack"
    two_stack = LayoutBlueprint(
        name="two_stack",
        description="Два изображения друг под другом",
        required_images=2,
        placements=[
            ImagePlacement(left=10.16, top=3.47, max_width=18.4, max_height=3.91),
            ImagePlacement(left=10.16, top=11.0, max_width=18.07, max_height=4.58),
        ],
    )
    registry.register(two_stack)
    print(f"✓ Зарегистрирован макет: {two_stack.name}")

    # Получение макета
    print(f"\nВсе макеты: {registry.list_all()}")

    layout = registry.get("single_wide")
    print(f"\nМакет '{layout.name}':")
    print(f"  Описание: {layout.description}")
    print(f"  Изображений: {layout.required_images}")
    print(f"  Размещений: {len(layout.placements)}")

    # Проверка существования
    print(f"\nМакет 'single_wide' существует: {registry.exists('single_wide')}")
    print(f"Макет 'unknown' существует: {registry.exists('unknown')}")
    print()


def example_validation_errors():
    """Пример обработки ошибок валидации."""
    print("=" * 60)
    print("Пример 4: Валидация и обработка ошибок")
    print("=" * 60)

    # Попытка создать слайд без заголовка
    try:
        slide = SlideConfig(
            layout_type="single_wide", title="", notes_source="Some notes", images=[]
        )
    except ValueError as e:
        print(f"✗ Ошибка при создании слайда: {e}")

    # Попытка создать презентацию без слайдов
    try:
        config = PresentationConfig(slides=[])
    except ValueError as e:
        print(f"✗ Ошибка при создании презентации: {e}")

    # Предупреждения при валидации
    config = PresentationConfig(
        slides=[
            SlideConfig(
                layout_type="single_wide",
                title="Слайд 1",
                notes_source="notes",
                images=[],  # Нет изображений!
            ),
            SlideConfig(
                layout_type="single_wide",
                title="Слайд 1",  # Дубликат заголовка!
                notes_source="notes",
                images=["img.png"],
            ),
        ]
    )

    warnings = validate_config(config)
    print(f"\nНайдено предупреждений: {len(warnings)}")
    for warning in warnings:
        print(f"  ⚠ {warning}")
    print()


if __name__ == "__main__":
    example_slide_config()
    example_presentation_config()
    example_layout_registry()
    example_validation_errors()

    print("=" * 60)
    print("Все примеры выполнены успешно!")
    print("=" * 60)
