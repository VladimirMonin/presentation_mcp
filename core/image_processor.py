"""
Процессор изображений для размещения на слайдах.

Этот модуль обеспечивает "умное" масштабирование изображений
с сохранением пропорций для вписывания в ограничивающий прямоугольник.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional, BinaryIO
import io

logger = logging.getLogger(__name__)

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
    logger.debug(f"🔄 Конвертация WebP в PNG: {image_path}")

    if Image is None:
        error_msg = "Pillow требуется для конвертации WebP изображений"
        logger.error(f"❌ {error_msg}")
        raise ImportError(error_msg)

    if image_path.suffix.lower() != ".webp":
        error_msg = f"Файл не является WebP: {image_path}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)

    try:
        # Открываем WebP
        with Image.open(image_path) as img:
            original_size = image_path.stat().st_size
            original_mode = img.mode

            logger.debug(
                f"🖼️ Информация об изображении: Format=WebP, Mode={original_mode}, Size={img.size[0]}x{img.size[1]}"
            )

            # Конвертируем в RGB если нужно (для прозрачности)
            if img.mode in ("RGBA", "LA", "P"):
                # Создаём белый фон для прозрачных изображений
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb_img.paste(
                    img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None
                )
                img = rgb_img
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Создаём буфер в памяти вместо временного файла
            png_buffer = io.BytesIO()

            # Сохраняем PNG в буфер
            img.save(png_buffer, "PNG", optimize=True)

            # Возвращаем указатель чтения в начало потока
            png_buffer.seek(0)

            png_size = len(png_buffer.getvalue())
            logger.debug(
                f"📊 Метрики конвертации: WebP {original_size} байт -> PNG {png_size} байт, Mode: {img.mode}"
            )

        return png_buffer

    except Exception as e:
        logger.error(f"❌ Ошибка конвертации изображения: {e}", exc_info=True)
        raise


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
    logger.debug(
        f"📐 Исходные размеры: Ограничитель: {max_width_cm}x{max_height_cm} см"
    )

    if Image is None:
        logger.warning("⚠️ Pillow не установлен. Невозможно вычислить размеры.")
        return None, None

    try:
        with Image.open(image_path) as img:
            img_width, img_height = img.size
            logger.debug(
                f"🖼️ Информация об изображении: Format={img.format}, Mode={img.mode}, Size={img_width}x{img_height}"
            )
    except FileNotFoundError:
        logger.error(f"❌ Файл изображения не найден: {image_path}")
        return None, None
    except Exception as e:
        logger.error(
            f"❌ Ошибка при чтении изображения {image_path}: {e}", exc_info=True
        )
        return None, None

    # Защита от деления на ноль
    if img_height == 0 or max_height_cm == 0:
        logger.warning(f"⚠️ Некорректные размеры для {image_path}")
        return None, None

    # Вычисляем соотношения сторон
    img_ratio = img_width / img_height
    box_ratio = max_width_cm / max_height_cm

    logger.debug(
        f"🎯 Логика масштабирования: Ratio исх={img_ratio:.2f}, цель={box_ratio:.2f}"
    )

    if img_ratio > box_ratio:
        # Изображение ШИРЕ коробки → ограничиваем по ШИРИНЕ
        # Высота будет вычислена автоматически для сохранения пропорций
        logger.debug("🎯 Выбор: Fit by WIDTH (изображение шире)")
        logger.debug(f"✂️ Вычисленные размеры: width={max_width_cm} см, height=AUTO")
        return max_width_cm, None
    else:
        # Изображение ВЫШЕ коробки (или одинаковое) → ограничиваем по ВЫСОТЕ
        # Ширина будет вычислена автоматически
        logger.debug("🎯 Выбор: Fit by HEIGHT (изображение выше)")
        logger.debug(f"✂️ Вычисленные размеры: width=AUTO, height={max_height_cm} см")
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
        logger.warning("⚠️ Pillow не установлен")
        return None

    try:
        with Image.open(image_path) as img:
            info = {
                "width": img.size[0],
                "height": img.size[1],
                "format": img.format,
                "mode": img.mode,
            }
            logger.debug(
                f"🖼️ Информация об изображении: Format={info['format']}, Mode={info['mode']}, Size={info['width']}x{info['height']}"
            )
            return info
    except Exception as e:
        logger.error(
            f"❌ Ошибка при получении информации об изображении: {e}", exc_info=True
        )
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
        logger.debug(
            f"⚠️ Pillow не установлен, проверка только существования файла: {image_path}"
        )
        return image_path.exists() and image_path.is_file()

    try:
        with Image.open(image_path) as img:
            img.verify()  # Проверка целостности
        logger.debug(f"✅ Изображение валидно: {image_path}")
        return True
    except Exception as e:
        logger.warning(
            f"⚠️ Изображение невалидно или повреждено: {image_path}, ошибка: {e}"
        )
        return False
