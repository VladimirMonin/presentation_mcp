"""
Анализатор шаблонов PowerPoint.

Этот модуль позволяет анализировать структуру .pptx шаблонов
для определения индексов заполнителей и параметров макетов.
"""

from pathlib import Path
from pptx import Presentation


def analyze_template(template_path: Path, layout_name: str = "VideoLayout") -> None:
    """
    Анализирует шаблон PPTX и выводит информацию о макетах и заполнителях.

    Args:
        template_path: Путь к файлу шаблона .pptx.
        layout_name: Имя макета для детального анализа (опционально).

    Example:
        >>> analyze_template(Path("template.pptx"), "VideoLayout")
    """
    try:
        prs = Presentation(str(template_path))
    except FileNotFoundError:
        print(f"✗ Ошибка: Файл не найден: {template_path}")
        return
    except Exception as e:
        print(f"✗ Ошибка загрузки шаблона: {e}")
        return

    print("=" * 70)
    print(f"📄 Анализ шаблона: {template_path.name}")
    print("=" * 70)
    print()

    # Вывод всех доступных макетов
    print("📋 Доступные макеты слайдов:")
    print()
    for i, layout in enumerate(prs.slide_layouts):
        print(f"  {i + 1}. {layout.name}")
    print()

    # Поиск нужного макета
    target_layout = None
    for layout in prs.slide_layouts:
        if layout.name == layout_name:
            target_layout = layout
            break

    if not target_layout:
        print(f"⚠ Макет '{layout_name}' не найден в шаблоне.")
        print("   Используйте один из перечисленных выше.")
        return

    # Детальный анализ макета
    print(f"🔍 Детальный анализ макета: '{layout_name}'")
    print("=" * 70)
    print()

    placeholders = target_layout.placeholders

    if not placeholders:
        print("  ⚠ В этом макете нет заполнителей (placeholders).")
        return

    print(f"  Найдено заполнителей: {len(placeholders)}")
    print()

    for ph in placeholders:
        print(f"  📌 Заполнитель IDX = {ph.placeholder_format.idx}")
        print(f"     Тип: {ph.placeholder_format.type}")
        print(f"     Имя: {ph.name}")

        # Попытка получить текст (если есть)
        try:
            if hasattr(ph, "text_frame") and ph.text_frame:
                sample_text = (
                    ph.text_frame.text[:50] if ph.text_frame.text else "(пусто)"
                )
                print(f"     Текст: {sample_text}")
        except Exception:
            pass

        print()

    print("=" * 70)
    print("✅ Анализ завершён")
    print()
    print("💡 Совет: Используйте IDX значения для конфигурации заполнителей")
    print("   в config/settings.py (PLACEHOLDER_TITLE_IDX и PLACEHOLDER_SLIDE_NUM_IDX)")
    print("=" * 70)


def list_layouts(template_path: Path) -> None:
    """
    Выводит простой список макетов в шаблоне.

    Args:
        template_path: Путь к файлу шаблона.
    """
    try:
        prs = Presentation(str(template_path))
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return

    print(f"\n📋 Макеты в {template_path.name}:\n")
    for i, layout in enumerate(prs.slide_layouts, 1):
        print(f"  {i}. {layout.name}")
    print()
