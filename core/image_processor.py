"""
Процессор изображений для размещения на слайдах.

Этот модуль обеспечивает "умное" масштабирование изображений
с сохранением пропорций для вписывания в ограничивающий прямоугольник.
"""

from pathlib import Path
from typing import Tuple, Optional, BinaryIO
import io

try:
    from PIL import Image
except ImportError:
    Image = None  # Graceful degradation


def convert_webp_to_png(image_path: Path) -> BinaryIO:
    """
    Конвертирует WebP изображение в PNG для совместимости с python-pptx.
    
    python-pptx поддерживает только: BMP, GIF, JPEG, PNG, TIFF, WMF.
    WebP не поддерживается, поэтому конвертируем его в PNG.
    
    Args:
        image_path: Путь к WebP изображению.
        
    Returns:
        Поток байтов (BytesIO) с PNG данными.
        
    Raises:
        ImportError: Если Pillow не установлен.
        ValueError: Если файл не является WebP.
    """
    if Image is None:
        raise ImportError("Pillow требуется для конвертации WebP изображений")
    
    if image_path.suffix.lower() != '.webp':
        raise ValueError(f"Файл не является WebP: {image_path}")
    
    # Открываем WebP
    with Image.open(image_path) as img:
        # Конвертируем в RGB если нужно (для прозрачности)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Создаём белый фон для прозрачных изображений
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Создаём буфер в памяти вместо временного файла
        png_buffer = io.BytesIO()
        
        # Сохраняем PNG в буфер
        img.save(png_buffer, 'PNG', optimize=True)
        
        # Возвращаем указатель чтения в начало потока
        png_buffer.seek(0)
        
    return png_buffer


def calculate_smart_dimensions(
    image_path: Path, max_width_cm: float, max_height_cm: float
) -> Tuple[Optional[float], Optional[float]]:
    """
    Вычисляет размеры для изображения с сохранением пропорций.

    Логика "умного" масштабирования:
    1. Загружает изображение и получает его реальные размеры.
    2. Вычисляет соотношение сторон изображения и "коробки" (bounding box).
    3. Если изображение шире коробки → фиксирует ширину, высота вычисляется автоматически.
    4. Если изображение выше коробки → фиксирует высоту, ширина вычисляется автоматически.

    Args:
        image_path: Путь к файлу изображения.
        max_width_cm: Максимальная ширина в сантиметрах.
        max_height_cm: Максимальная высота в сантиметрах.

    Returns:
        Кортеж (width, height), где один из параметров None (для автовычисления).
        Возвращает (None, None) в случае ошибки.

    Note:
        - Возвращаемые значения в сантиметрах (float), не в единицах python-pptx.
        - Конвертация в Cm() выполняется в слое презентации, а не здесь.

    Example:
        >>> # Широкое изображение 1920x1080
        >>> w, h = calculate_smart_dimensions(Path("wide.png"), 20.0, 10.0)
        >>> # Результат: (20.0, None) - ограничим ширину
        >>>
        >>> # Высокое изображение 1080x1920
        >>> w, h = calculate_smart_dimensions(Path("tall.png"), 10.0, 15.0)
        >>> # Результат: (None, 15.0) - ограничим высоту
    """
    if Image is None:
        print("⚠ Предупреждение: Pillow не установлен. Невозможно вычислить размеры.")
        return None, None

    try:
        with Image.open(image_path) as img:
            img_width, img_height = img.size
    except FileNotFoundError:
        print(f"✗ Ошибка: Файл изображения не найден: {image_path}")
        return None, None
    except Exception as e:
        print(f"✗ Ошибка при чтении изображения {image_path}: {e}")
        return None, None

    # Защита от деления на ноль
    if img_height == 0 or max_height_cm == 0:
        print(f"⚠ Предупреждение: Некорректные размеры для {image_path}")
        return None, None

    # Вычисляем соотношения сторон
    img_ratio = img_width / img_height
    box_ratio = max_width_cm / max_height_cm

    if img_ratio > box_ratio:
        # Изображение ШИРЕ коробки → ограничиваем по ШИРИНЕ
        # Высота будет вычислена автоматически для сохранения пропорций
        return max_width_cm, None
    else:
        # Изображение ВЫШЕ коробки (или одинаковое) → ограничиваем по ВЫСОТЕ
        # Ширина будет вычислена автоматически
        return None, max_height_cm


def get_image_info(image_path: Path) -> Optional[dict]:
    """
    Получает информацию об изображении без вычисления размеров.

    Args:
        image_path: Путь к изображению.

    Returns:
        Словарь с ключами 'width', 'height', 'format' или None при ошибке.

    Example:
        >>> info = get_image_info(Path("image.png"))
        >>> print(f"Размер: {info['width']}x{info['height']}")
        >>> print(f"Формат: {info['format']}")
    """
    if Image is None:
        return None

    try:
        with Image.open(image_path) as img:
            return {
                "width": img.size[0],
                "height": img.size[1],
                "format": img.format,
                "mode": img.mode,
            }
    except Exception as e:
        print(f"✗ Ошибка при получении информации об изображении: {e}")
        return None


def validate_image(image_path: Path) -> bool:
    """
    Проверяет, является ли файл валидным изображением.

    Args:
        image_path: Путь к изображению.

    Returns:
        True, если изображение валидно и может быть загружено.

    Example:
        >>> if validate_image(Path("picture.jpg")):
        ...     print("Изображение ОК")
        ... else:
        ...     print("Изображение повреждено")
    """
    if Image is None:
        # Без Pillow не можем проверить
        return image_path.exists() and image_path.is_file()

    try:
        with Image.open(image_path) as img:
            img.verify()  # Проверка целостности
        return True
    except Exception:
        return False
