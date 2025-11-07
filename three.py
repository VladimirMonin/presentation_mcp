from pptx import Presentation
from pptx.util import Inches
import json
import sys
from two import clean_markdown_for_notes  # Импортируем наш очиститель

# -----------------------------------------------------------------
# --- "КОНТРАКТ API" (Получено из analyze_template.py) ---
# -----------------------------------------------------------------
TEMPLATE_FILE = "template.pptx"
TARGET_LAYOUT_NAME = "VideoLayout"  # Имя макета из "Образца слайдов"

# ID Заполнителей (замени на свои, полученные от анализатора)
IDX_TITLE = 11  # Пример: idx для Заголовка
IDX_SLIDE_NUM = 10  # Пример: idx для Номера слайда

# -----------------------------------------------------------------
# --- "ЧЕРТЕЖИ" МАКЕТОВ (layout_type) ---
# -----------------------------------------------------------------

# --- Макет 'single' (1 картинка) ---
# (Координаты измеряются в PowerPoint один раз и хардкодятся)
SINGLE_IMG_LEFT = Inches(4.5)
SINGLE_IMG_TOP = Inches(1.5)
SINGLE_IMG_WIDTH = Inches(5.0)

# --- Макет 'two_horizontal_stack' (2 картинки в столбик) ---
STACK_LEFT = Inches(4.5)
STACK_WIDTH = Inches(5.0)
STACK_TOP_1 = Inches(1.0)
STACK_TOP_2 = Inches(4.2)  # Отступ от первой

# ... (Добавь сюда константы для 'two_squares' и других макетов) ...
# -----------------------------------------------------------------


def load_slide_data(json_path: str) -> list:
    """Загружает данные о слайдах из JSON-файла."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("slides", [])
    except FileNotFoundError:
        print(f"Ошибка: JSON-файл не найден: {json_path}")
        return []
    except json.JSONDecodeError:
        print(f"Ошибка: Некорректный JSON в файле: {json_path}")
        return []


def generate_presentation(slide_data: list, template_path: str, output_path: str):
    """
    Основная функция генерации презентации.
    """
    try:
        prs = Presentation(template_path)
    except Exception as e:
        print(f"Критическая ошибка: Не могу загрузить шаблон '{template_path}'. {e}")
        return

    # Ищем наш кастомный макет по имени
    slide_layout = next(
        (layout for layout in prs.slide_layouts if layout.name == TARGET_LAYOUT_NAME),
        None,
    )
    if not slide_layout:
        print(f"Критическая ошибка: Макет '{TARGET_LAYOUT_NAME}' не найден в шаблоне.")
        return

    # --- Применение "Обходного пути" бага PowerPoint 2013 ---
    for slide in prs.slides:
        _ = slide.notes_slide

    # --- Главный цикл создания слайдов ---
    for i, item in enumerate(slide_data):
        print(f"Создание слайда {i + 1}...")
        slide = prs.slides.add_slide(slide_layout)

        # --- Обходной путь бага 2013 (для *каждого* нового слайда) ---
        _ = slide.notes_slide

        # --- 1. Заполнение текста ---
        try:
            # Заголовок
            title_ph = slide.shapes.placeholders[IDX_TITLE]
            title_ph.text_frame.text = item.get("title", "Без заголовка")

            # Номер слайда (просто как текст)
            num_ph = slide.shapes.placeholders[IDX_SLIDE_NUM]
            num_ph.text_frame.text = str(i + 1)  # Авто-нумерация

        except KeyError:
            print(
                f"Предупреждение: не найдены заполнители (idx {IDX_TITLE} или {IDX_SLIDE_NUM})."
            )

        # --- 2. Добавление заметок докладчика (с очисткой) ---
        notes_text = item.get("notes_text", "")
        clean_notes = clean_markdown_for_notes(notes_text)
        slide.notes_slide.notes_text_frame.text = clean_notes

        # --- 3. Размещение скриншотов по "Чертежам" ---
        layout_type = item.get("layout_type", "single")
        images = item.get("images", [])

        try:
            if layout_type == "single" and images:
                slide.shapes.add_picture(
                    images[0], SINGLE_IMG_LEFT, SINGLE_IMG_TOP, width=SINGLE_IMG_WIDTH
                )

            elif layout_type == "two_horizontal_stack" and len(images) >= 2:
                # 1-я картинка
                slide.shapes.add_picture(
                    images[0], STACK_LEFT, STACK_TOP_1, width=STACK_WIDTH
                )
                # 2-я картинка
                slide.shapes.add_picture(
                    images[1], STACK_LEFT, STACK_TOP_2, width=STACK_WIDTH
                )

            # elif layout_type == 'two_squares' and len(images) >= 2:
            #   ... (добавь сюда свою логику и константы) ...

            else:
                if images:
                    print(
                        f"Предупреждение: Неизвестный layout_type '{layout_type}' или неверное кол-во картинок."
                    )

        except FileNotFoundError as e:
            print(f"  Ошибка: Файл скриншота не найден: {e.filename}")
        except Exception as e:
            print(f"  Не удалось добавить картинку: {e}")

    # --- 4. Сохранение результата ---
    try:
        prs.save(output_path)
        print(f"\nПрезентация успешно сохранена: '{output_path}'")
    except Exception as e:
        print(f"Ошибка сохранения файла: {e}")


# --- Запуск ---
if __name__ == "__main__":
    # Входной JSON-конфиг (от ИИ-агента или созданный вручную)
    INPUT_JSON = "slides_config.json"
    OUTPUT_FILE = "generated_presentation3.pptx"

    slide_data = load_slide_data(INPUT_JSON)
    if slide_data:
        generate_presentation(slide_data, TEMPLATE_FILE, OUTPUT_FILE)
