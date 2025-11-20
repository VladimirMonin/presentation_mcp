# Пакет исходного кода проекта: presentation_mcp

## `.pytest_cache/README.md`

```md
# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.

```

## `cli/__init__.py`

```py
"""
Интерфейс командной строки Auto-Slide.

Этот пакет содержит CLI команды для:
- Генерации презентаций (generate)
- Анализа шаблонов (analyze)
"""

from .commands import (
    cmd_generate,
    cmd_analyze,
    cmd_help,
    parse_args,
)

__all__ = [
    "cmd_generate",
    "cmd_analyze",
    "cmd_help",
    "parse_args",
]

```

## `cli/commands.py`

```py
"""
CLI команды для Auto-Slide.

Этот модуль содержит команды командной строки для генерации
презентаций и анализа шаблонов.
"""

import logging
from pathlib import Path
from typing import Optional

from models import LayoutRegistry
from io_handlers import PathResolver, ConfigLoader, ResourceLoader
from core import PresentationBuilder, analyze_template
from config import register_default_layouts

logger = logging.getLogger(__name__)


def cmd_generate(
    config_path: str,
    output: Optional[str] = None,
    template: Optional[str] = None,
    verbose: bool = True,
) -> int:
    """
    Генерирует презентацию из JSON конфигурации.

    Args:
        config_path: Путь к JSON файлу конфигурации.
        output: Переопределить путь к выходному файлу (опционально).
        template: Переопределить путь к шаблону (опционально).
        verbose: Выводить ли подробную информацию.

    Returns:
        0 при успехе, код ошибки при неудаче.

    Example:
        >>> cmd_generate("slides_config.json")
        >>> cmd_generate("config.json", output="my_presentation.pptx")
    """
    logger.info(f"▶️ Запущена команда generate. Config: {config_path}, Output: {output or 'default'}")
    logger.debug(f"🔍 Параметры: template={template or 'default'}, verbose={verbose}")
    
    try:
        # Шаг 1: Загрузка конфигурации
        config_path_obj = Path(config_path).resolve()

        if not config_path_obj.exists():
            logger.error(f"❌ Файл конфигурации не найден: {config_path}")
            return 1

        logger.debug(f"� Загрузка конфигурации: {config_path_obj}")
        config = ConfigLoader.load(config_path_obj)

        # Применение переопределений из CLI
        if output:
            logger.debug(f"🔧 Override output: {output}")
            config.output_path = output
        if template:
            logger.debug(f"🔧 Override template: {template}")
            config.template_path = template

        # Шаг 2: Настройка компонентов
        logger.debug("🔧 Инициализация компонентов")
        resolver = PathResolver(config_path_obj)  # Для ресурсов (images, audio)
        loader = ResourceLoader(resolver)
        registry = LayoutRegistry()
        register_default_layouts(registry)

        # Шаг 3: Сборка презентации
        builder = PresentationBuilder(registry, loader, verbose=verbose)

        # Шаблон резолвим от ТЕКУЩЕЙ директории (откуда запущен CLI)
        template_path = Path(config.template_path)
        if not template_path.is_absolute():
            template_path = Path.cwd() / template_path
        template_path = template_path.resolve()
        
        logger.debug(f"📄 Путь к шаблону (от CWD): {template_path}")

        if not template_path.exists():
            logger.error(f"❌ Шаблон не найден: {template_path}")
            return 1

        prs = builder.build(config, template_path)

        if prs is None:
            logger.critical("💥 Критическая ошибка при сборке презентации", exc_info=True)
            return 1

        # Шаг 4: Сохранение
        # Output тоже от текущей директории
        output_path = Path(config.output_path)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        output_path = output_path.resolve()
        
        logger.debug(f"💾 Путь к выходному файлу (от CWD): {output_path}")
        builder.save(prs, output_path)

        # Проверка на ошибки
        errors = builder.get_errors()
        if errors:
            logger.warning(f"⚠️ Завершено с {len(errors)} некритичными ошибками")
            return 2  # Частичный успех

        logger.info("✅ Генерация завершена успешно")
        return 0  # Полный успех

    except FileNotFoundError as e:
        logger.error(f"❌ Файл не найден: {e}", exc_info=True)
        return 1
    except ValueError as e:
        logger.error(f"❌ Ошибка валидации: {e}", exc_info=True)
        return 1
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка при генерации: {e}", exc_info=True)
        return 1


def cmd_analyze(
    template_path: str, layout: str = "VideoLayout", list_only: bool = False
) -> int:
    """
    Анализирует шаблон PPTX.

    Args:
        template_path: Путь к файлу шаблона.
        layout: Имя макета для детального анализа.
        list_only: Показать только список макетов (без деталей).

    Returns:
        0 при успехе, 1 при ошибке.

    Example:
        >>> cmd_analyze("template.pptx")
        >>> cmd_analyze("template.pptx", layout="CustomLayout")
        >>> cmd_analyze("template.pptx", list_only=True)
    """
    logger.info(f"▶️ Запущена команда analyze для {template_path}")
    logger.debug(f"🔍 Параметры: layout={layout}, list_only={list_only}")
    
    try:
        template_path_obj = Path(template_path).resolve()

        if not template_path_obj.exists():
            logger.error(f"❌ Файл не найден: {template_path}")
            return 1

        if list_only:
            logger.debug("📋 Режим: только список макетов")
            from core import list_layouts

            list_layouts(template_path_obj)
        else:
            logger.debug(f"🔍 Анализ макета: {layout}")
            analyze_template(template_path_obj, layout)

        logger.info("✅ Анализ завершен успешно")
        return 0

    except Exception as e:
        logger.error(f"❌ Ошибка при анализе: {e}", exc_info=True)
        return 1


def cmd_help() -> None:
    """Выводит справку по использованию CLI."""
    logger.info("❓ Запрошена справка")
    
    help_text = """
╔══════════════════════════════════════════════════════════════════╗
║                  Auto-Slide: PowerPoint Automation               ║
╚══════════════════════════════════════════════════════════════════╝

📖 ИСПОЛЬЗОВАНИЕ:

  python main.py <команда> [аргументы]

📋 КОМАНДЫ:

  generate <config.json> [опции]
    Генерирует презентацию из JSON конфигурации
    
    Опции:
      -o, --output <файл>     Путь к выходному файлу
      -t, --template <файл>   Путь к шаблону PPTX
      -q, --quiet            Минимальный вывод
    
    Примеры:
      python main.py generate slides_config.json
      python main.py generate config.json -o my_slides.pptx
      python main.py generate config.json -t custom_template.pptx

  analyze <template.pptx> [опции]
    Анализирует структуру шаблона PPTX
    
    Опции:
      -l, --layout <имя>     Имя макета для анализа (по умолчанию: VideoLayout)
      --list                 Показать только список макетов
    
    Примеры:
      python main.py analyze template.pptx
      python main.py analyze template.pptx -l CustomLayout
      python main.py analyze template.pptx --list

  help
    Показывает эту справку

📄 ФОРМАТ JSON:

  {
    "template_path": "template.pptx",
    "output_path": "output.pptx",
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

🔗 ДОКУМЕНТАЦИЯ:

  Подробная документация: doc/README.md
  План рефакторинга: doc/plan/refactor_plan.md

╔══════════════════════════════════════════════════════════════════╗
║  GitHub Copilot | 2025                                           ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(help_text)


def parse_args(args: list) -> int:
    """
    Парсит аргументы командной строки и выполняет команды.

    Args:
        args: Список аргументов (обычно sys.argv[1:]).

    Returns:
        Exit code (0 = success, >0 = error).
    """
    logger.debug(f"🔍 Парсинг аргументов CLI: {args}")
    
    if not args or args[0] in ["help", "--help", "-h"]:
        logger.debug("📋 Вызвана справка")
        cmd_help()
        return 0

    command = args[0]
    logger.debug(f"🔧 Команда: {command}")

    if command == "generate":
        if len(args) < 2:
            logger.error("❌ Не указан файл конфигурации для generate")
            return 1

        config_path = args[1]
        output = None
        template = None
        verbose = True

        # Парсинг опций
        i = 2
        while i < len(args):
            if args[i] in ["-o", "--output"] and i + 1 < len(args):
                output = args[i + 1]
                logger.debug(f"🔧 CLI опция: output={output}")
                i += 2
            elif args[i] in ["-t", "--template"] and i + 1 < len(args):
                template = args[i + 1]
                logger.debug(f"🔧 CLI опция: template={template}")
                i += 2
            elif args[i] in ["-q", "--quiet"]:
                verbose = False
                logger.debug("🔧 CLI опция: quiet mode")
                i += 1
            else:
                logger.warning(f"⚠️ Неизвестная опция CLI: {args[i]}")
                i += 1

        return cmd_generate(config_path, output, template, verbose)

    elif command == "analyze":
        if len(args) < 2:
            logger.error("❌ Не указан файл шаблона для analyze")
            return 1

        template_path = args[1]
        layout = "VideoLayout"
        list_only = False

        # Парсинг опций
        i = 2
        while i < len(args):
            if args[i] in ["-l", "--layout"] and i + 1 < len(args):
                layout = args[i + 1]
                logger.debug(f"🔧 CLI опция: layout={layout}")
                i += 2
            elif args[i] == "--list":
                list_only = True
                logger.debug("🔧 CLI опция: list only mode")
                i += 1
            else:
                logger.warning(f"⚠️ Неизвестная опция CLI: {args[i]}")
                i += 1

        return cmd_analyze(template_path, layout, list_only)

    else:
        logger.error(f"❌ Неизвестная команда: {command}")
        return 1

```

## `cline_mcp_settings.json`

```json
{
  "mcpServers": {
    "presentation-builder": {
      "autoApprove": ["generate_presentation"],
      "disabled": false,
      "timeout": 120,
      "type": "stdio",
      "command": "C:/PY/presentation_mcp/.venv/Scripts/python.exe",
      "args": ["C:/PY/presentation_mcp/mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}

```

## `config/__init__.py`

```py
"""
Конфигурация проекта Auto-Slide.

Этот пакет содержит настройки по умолчанию, константы и регистрацию макетов.
"""

from .settings import (
    register_default_layouts,
    DEFAULT_TEMPLATE_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_LAYOUT_NAME,
    PLACEHOLDER_TITLE_IDX,
    PLACEHOLDER_SLIDE_NUM_IDX,
    PLACEHOLDER_TITLE_LAYOUT_TITLE_IDX,
    PLACEHOLDER_TITLE_LAYOUT_SLIDE_NUM_IDX,
    PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX,
)

__all__ = [
    "register_default_layouts",
    "DEFAULT_TEMPLATE_PATH",
    "DEFAULT_OUTPUT_PATH",
    "DEFAULT_LAYOUT_NAME",
    "PLACEHOLDER_TITLE_IDX",
    "PLACEHOLDER_SLIDE_NUM_IDX",
    "PLACEHOLDER_TITLE_LAYOUT_TITLE_IDX",
    "PLACEHOLDER_TITLE_LAYOUT_SLIDE_NUM_IDX",
    "PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX",
]

```

## `config/settings.py`

```py
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

# ID заполнителей в шаблоне youtube_base.pptx
# VideoLayout (контентные слайды):
PLACEHOLDER_TITLE_IDX = 10
PLACEHOLDER_SLIDE_NUM_IDX = 11

# TitleLayout (титульные слайды YouTube):
PLACEHOLDER_TITLE_LAYOUT_TITLE_IDX = 10
PLACEHOLDER_TITLE_LAYOUT_SLIDE_NUM_IDX = 12
PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX = 13

```

## `core/__init__.py`

```py
"""
Ядро бизнес-логики Auto-Slide.

Этот пакет содержит основные компоненты:
- Анализатор шаблонов
- Очиститель Markdown
- Процессор изображений
- Построитель презентаций
- Система логирования
"""

from .logger import setup_logging
from .markdown_cleaner import (
    clean_markdown_for_notes,
    clean_markdown_preserve_structure,
    validate_markdown,
)
from .image_processor import (
    calculate_smart_dimensions,
    get_image_info,
    validate_image,
    convert_webp_to_png,
)
from .presentation_builder import PresentationBuilder
from .template_analyzer import analyze_template, list_layouts

__all__ = [
    "setup_logging",
    "clean_markdown_for_notes",
    "clean_markdown_preserve_structure",
    "validate_markdown",
    "calculate_smart_dimensions",
    "get_image_info",
    "validate_image",
    "convert_webp_to_png",
    "PresentationBuilder",
    "analyze_template",
    "list_layouts",
]

```

## `core/image_processor.py`

```py
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

```

## `core/logger.py`

```py
"""
Централизованная система логирования для Presentation Builder.

Настраивает три потока логов:
1. Console (stdout) - INFO или DEBUG с --verbose
2. logs/app.log - полная история (DEBUG)
3. logs/error.log - только ошибки (ERROR+)

Использует RotatingFileHandler для автоматической ротации файлов.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


class SafeConsoleHandler(logging.StreamHandler):
    """
    StreamHandler с защитой от UnicodeEncodeError в Windows console (cp1251).
    При ошибке кодировки заменяет эмодзи и другие символы на '?' вместо краша.
    """

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Попытка записать с родной кодировкой
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # Fallback: заменяем непечатаемые символы на '?'
            try:
                msg = self.format(record)
                # Кодируем с заменой эмодзи на '?', затем декодируем обратно
                encoding = self.stream.encoding or "utf-8"
                safe_msg = msg.encode(encoding, errors="replace").decode(encoding)
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)
        except Exception:
            self.handleError(record)


def setup_logging(verbose: bool = False, log_dir: str = "logs"):
    """
    Настраивает глобальный логгер приложения.

    Args:
        verbose: Если True, выводит DEBUG в консоль (по умолчанию только INFO)
        log_dir: Директория для файлов логов (по умолчанию "logs")

    Структура:
        - Console: INFO (или DEBUG при verbose)
        - logs/app.log: DEBUG (все детали + ротация 5MB × 3)
        - logs/error.log: ERROR (только ошибки + ротация 5MB × 3)
    """
    # 1. Создаем директорию для логов
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 2. Базовый форматтер
    # Пример: [2025-11-20 14:00:01] INFO     core.builder:45 - 🚀 Начало сборки
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-8s %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Упрощенный форматтер для консоли в обычном режиме
    console_formatter_simple = logging.Formatter("%(levelname)-8s %(message)s")

    # 3. Получаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Ловим всё, фильтруем на хендлерах

    # Очищаем существующие хендлеры (чтобы не дублировались при перезапуске)
    root_logger.handlers.clear()

    # --- HANDLER 1: CONSOLE (с защитой от emoji в Windows) ---
    console_handler = SafeConsoleHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # В verbose режиме показываем полный формат, иначе упрощенный
    if verbose:
        console_handler.setFormatter(formatter)
    else:
        console_handler.setFormatter(console_formatter_simple)

    root_logger.addHandler(console_handler)

    # --- HANDLER 2: APP.LOG (Full Debug) ---
    # RotatingFileHandler не даст файлу разрастись до гигабайт
    # 5 МБ на файл, храним 3 последних архива
    app_log_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    app_log_handler.setLevel(logging.DEBUG)
    app_log_handler.setFormatter(formatter)
    root_logger.addHandler(app_log_handler)

    # --- HANDLER 3: ERROR.LOG (Errors Only) ---
    error_log_handler = RotatingFileHandler(
        log_path / "error.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    error_log_handler.setLevel(logging.ERROR)
    error_log_handler.setFormatter(formatter)
    root_logger.addHandler(error_log_handler)

    # Сообщение о том, что логирование инициализировано
    logging.info("⚙️ Система логирования инициализирована")
    logging.debug(f"📂 Логи сохраняются в: {log_path.resolve()}")

```

## `core/markdown_cleaner.py`

```py
"""
Очистка Markdown текста для заметок докладчика.

Этот модуль преобразует Markdown разметку в чистый читаемый текст,
удаляя все элементы форматирования, но сохраняя структуру и читаемость.
"""

import logging
import markdown
from bs4 import BeautifulSoup
from typing import Optional

logger = logging.getLogger(__name__)


def clean_markdown_for_notes(md_text: str) -> str:
    """
    Конвертирует Markdown в чистый текст для заметок докладчика.

    Процесс:
    1. Markdown → HTML (через библиотеку markdown)
    2. HTML → plain text (через BeautifulSoup)
    3. Очистка от лишних пустых строк
    4. Нормализация пробелов

    Args:
        md_text: Текст в формате Markdown.

    Returns:
        Чистый текст без форматирования, готовый для заметок.

    Note:
        - Списки превращаются в строки без маркеров
        - Жирный/курсив удаляются
        - Ссылки превращаются в текст
        - Заголовки становятся обычным текстом
        - Код-блоки сохраняются как текст

    Example:
        >>> md = "# Заголовок\\n\\n- Пункт **жирный**\\n- Другой"
        >>> clean = clean_markdown_for_notes(md)
        >>> print(clean)
        Заголовок
        Пункт жирный
        Другой
    """
    if not md_text:
        logger.debug("🧹 Пустой входной текст, возвращаем пустую строку")
        return ""

    input_length = len(md_text)
    logger.debug(f"🧹 Очистка Markdown, длина входа: {input_length} символов")

    try:
        # Шаг 1: Конвертируем Markdown в HTML
        html = markdown.markdown(md_text)
        logger.debug(f"🔧 Markdown → HTML: {len(html)} символов")

        # Шаг 2: Парсим HTML с BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Шаг 3: Извлекаем текст (BeautifulSoup автоматически убирает теги)
        # separator="\n" сохраняет структуру абзацев
        text = soup.get_text(separator="\n").strip()

        # Шаг 4: Очистка от множественных пустых строк
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        output_length = len(clean_text)
        logger.debug(f"✨ Очистка завершена, длина выхода: {output_length} символов")

        return clean_text

    except Exception as e:
        # В случае ошибки возвращаем исходный текст
        # (лучше показать что-то, чем ничего)
        logger.error(f"❌ Ошибка очистки Markdown: {e}", exc_info=True)
        return md_text


def clean_markdown_preserve_structure(md_text: str) -> str:
    """
    Очищает Markdown с сохранением структуры абзацев и отступов.

    В отличие от clean_markdown_for_notes, эта функция сохраняет
    пустые строки между абзацами для лучшей читаемости.

    Args:
        md_text: Текст в формате Markdown.

    Returns:
        Чистый текст с сохранением структуры параграфов.

    Example:
        >>> md = "Первый параграф.\\n\\nВторой параграф."
        >>> clean = clean_markdown_preserve_structure(md)
        >>> print(clean)
        Первый параграф.

        Второй параграф.
    """
    if not md_text:
        logger.debug("🧹 Пустой входной текст (preserve_structure)")
        return ""

    logger.debug(f"🧹 Очистка Markdown с сохранением структуры, длина: {len(md_text)} символов")

    try:
        html = markdown.markdown(md_text)
        soup = BeautifulSoup(html, "html.parser")

        # Обрабатываем каждый блочный элемент отдельно
        blocks = []
        for element in soup.find_all(
            ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"]
        ):
            text = element.get_text().strip()
            if text:
                blocks.append(text)

        # Соединяем блоки двойным переводом строки
        result = "\n\n".join(blocks)
        logger.debug(f"✨ Очистка с сохранением структуры завершена: {len(result)} символов")
        return result

    except Exception as e:
        logger.error(f"❌ Ошибка очистки Markdown (preserve_structure): {e}", exc_info=True)
        return md_text


def validate_markdown(md_text: str) -> Optional[str]:
    """
    Проверяет корректность Markdown текста.

    Args:
        md_text: Текст для валидации.

    Returns:
        None, если текст валиден.
        Строка с описанием ошибки, если найдена проблема.

    Example:
        >>> error = validate_markdown("# Заголовок\\n\\nТекст")
        >>> if error:
        ...     print(f"Ошибка: {error}")
    """
    logger.debug(f"🔍 Валидация Markdown, длина: {len(md_text) if md_text else 0} символов")
    
    if not md_text:
        logger.warning("⚠️ Валидация: пустой текст")
        return "Пустой текст"

    try:
        # Пытаемся преобразовать
        html = markdown.markdown(md_text)

        # Базовая проверка результата
        if not html or html.isspace():
            logger.warning("⚠️ Валидация: Markdown преобразовался в пустой HTML")
            return "Markdown преобразовался в пустой HTML"

        logger.debug("✅ Валидация Markdown успешна")
        return None  # Всё ОК

    except Exception as e:
        error_msg = f"Ошибка парсинга: {str(e)}"
        logger.error(f"❌ Валидация Markdown: {error_msg}", exc_info=True)
        return error_msg


# Тестовые кейсы (для документации и проверки)

TEST_CASES = [
    {
        "name": "Простой текст",
        "input": "Просто текст без разметки.",
        "expected": "Просто текст без разметки.",
    },
    {
        "name": "Жирный и курсив",
        "input": "Текст с **жирным** и *курсивом*.",
        "expected": "Текст с жирным и курсивом.",
    },
    {
        "name": "Заголовки",
        "input": "# Заголовок 1\n## Заголовок 2\nТекст",
        "expected": "Заголовок 1\nЗаголовок 2\nТекст",
    },
    {
        "name": "Списки",
        "input": "- Первый пункт\n- Второй пункт\n- Третий пункт",
        "expected": "Первый пункт\nВторой пункт\nТретий пункт",
    },
    {
        "name": "Нумерованные списки",
        "input": "1. Один\n2. Два\n3. Три",
        "expected": "Один\nДва\nТри",
    },
    {
        "name": "Ссылки",
        "input": "Посмотрите [эту ссылку](https://example.com).",
        "expected": "Посмотрите эту ссылку.",
    },
    {
        "name": "Код inline",
        "input": "Используйте `код` в тексте.",
        "expected": "Используйте код в тексте.",
    },
    {
        "name": "Блок кода",
        "input": "```python\nprint('hello')\n```",
        "expected": "print('hello')",
    },
    {"name": "Пустой текст", "input": "", "expected": ""},
    {
        "name": "Множественные пустые строки",
        "input": "Первая строка\n\n\n\nВторая строка",
        "expected": "Первая строка\nВторая строка",
    },
]


def run_tests() -> bool:
    """
    Запускает тестовые кейсы для проверки работы функции.

    Returns:
        True, если все тесты прошли успешно, иначе False.
    """
    print("=" * 60)
    print("ТЕСТЫ: Очистка Markdown")
    print("=" * 60)

    passed = 0
    failed = 0

    for test in TEST_CASES:
        result = clean_markdown_for_notes(test["input"])

        if result == test["expected"]:
            passed += 1
            print(f"✓ {test['name']}")
        else:
            failed += 1
            print(f"✗ {test['name']}")
            print(f"  Ожидалось: {repr(test['expected'])}")
            print(f"  Получено:  {repr(result)}")

    print()
    print(f"Пройдено: {passed}/{len(TEST_CASES)}")
    print(f"Провалено: {failed}/{len(TEST_CASES)}")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    # Запуск тестов при прямом вызове модуля
    success = run_tests()
    exit(0 if success else 1)

```

## `core/presentation_builder.py`

```py
"""
Построитель презентаций PowerPoint.

Этот модуль содержит главный оркестратор, который собирает все компоненты
вместе для генерации итоговой презентации.
"""

import logging
from pathlib import Path
from typing import Optional
from pptx import Presentation
from pptx.util import Cm

from models import PresentationConfig, LayoutRegistry
from models.slide_types import BaseSlideConfig, YouTubeTitleSlideConfig
from io_handlers import ResourceLoader
from core import (
    clean_markdown_for_notes,
    calculate_smart_dimensions,
    convert_webp_to_png,
)
from config import (
    PLACEHOLDER_TITLE_IDX,
    PLACEHOLDER_SLIDE_NUM_IDX,
    PLACEHOLDER_TITLE_LAYOUT_TITLE_IDX,
    PLACEHOLDER_TITLE_LAYOUT_SLIDE_NUM_IDX,
    PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX,
)

logger = logging.getLogger(__name__)


class PresentationBuilder:
    """
    Оркестратор сборки презентации из конфигурации.

    Основной компонент, который:
    1. Загружает шаблон PPTX
    2. Создаёт слайды согласно конфигурации
    3. Размещает контент (текст, изображения, заметки)
    4. Сохраняет итоговый файл

    Attributes:
        layout_registry: Реестр макетов для размещения изображений.
        resource_loader: Загрузчик ресурсов (MD файлов, изображений).
        idx_title: Индекс заполнителя для заголовка.
        idx_slide_num: Индекс заполнителя для номера слайда.

    Example:
        >>> from models import LayoutRegistry
        >>> from io_handlers import ResourceLoader, PathResolver
        >>> from config import register_default_layouts
        >>>
        >>> resolver = PathResolver(Path("config.json"))
        >>> loader = ResourceLoader(resolver)
        >>> registry = LayoutRegistry()
        >>> register_default_layouts(registry)
        >>>
        >>> builder = PresentationBuilder(registry, loader)
        >>> prs = builder.build(config, Path("template.pptx"))
        >>> builder.save(prs, Path("output.pptx"))
    """

    def __init__(
        self,
        layout_registry: LayoutRegistry,
        resource_loader: ResourceLoader,
        idx_title: int = PLACEHOLDER_TITLE_IDX,
        idx_slide_num: int = PLACEHOLDER_SLIDE_NUM_IDX,
        verbose: bool = True,
    ):
        """
        Инициализация построителя.

        Args:
            layout_registry: Реестр макетов слайдов.
            resource_loader: Загрузчик ресурсов.
            idx_title: Индекс заполнителя заголовка (по умолчанию из config).
            idx_slide_num: Индекс заполнителя номера слайда.
            verbose: Выводить ли подробные сообщения о процессе.
        """
        self.layouts = layout_registry
        self.loader = resource_loader
        self.idx_title = idx_title
        self.idx_slide_num = idx_slide_num
        self.verbose = verbose

        self._errors = []  # Список ошибок, накопленных в процессе

        logger.debug(
            f"⚙️ Инициализация PresentationBuilder: idx_title={idx_title}, idx_slide_num={idx_slide_num}"
        )

    def build(
        self, config: PresentationConfig, template_path: Path
    ) -> Optional[Presentation]:
        """
        Главный метод сборки презентации.

        Args:
            config: Конфигурация презентации.
            template_path: Путь к файлу шаблона .pptx.

        Returns:
            Объект Presentation или None при критической ошибке.

        Raises:
            FileNotFoundError: Если шаблон не найден.
            ValueError: Если макет не найден в шаблоне.
        """
        self._errors = []  # Сброс ошибок

        logger.info(f"🚀 Начало сборки презентации из шаблона: {template_path}")
        logger.debug(f"📂 Полный путь к шаблону: {template_path.resolve()}")

        # Шаг 1: Загрузка шаблона
        logger.debug(f"� Загрузка шаблона: {template_path}")

        try:
            prs = Presentation(str(template_path))
            logger.debug(f"✅ Шаблон загружен, слайдов в мастере: {len(prs.slide_layouts)}")
        except FileNotFoundError:
            logger.error(f"❌ Шаблон не найден: {template_path}")
            raise FileNotFoundError(f"Шаблон не найден: {template_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки шаблона: {e}", exc_info=True)
            raise ValueError(f"Ошибка загрузки шаблона: {e}")

        # Шаг 2: Применение workaround для PowerPoint 2013
        # (Инициализация notes_slide для всех существующих слайдов)
        for slide in prs.slides:
            _ = slide.notes_slide

        # Шаг 3: Создание слайдов
        logger.info(f"� Создание {len(config.slides)} слайдов...")
        logger.debug(f"🔍 Глобальный макет: {config.layout_name}")

        for i, slide_cfg in enumerate(config.slides, 1):
            try:
                # Определяем макет для этого слайда
                # Если в слайде указан layout_name - используем его, иначе глобальный
                current_layout_name = slide_cfg.layout_name or config.layout_name
                
                if slide_cfg.layout_name:
                    logger.debug(f"🎭 Слайд #{i}: локальный макет '{current_layout_name}' (override)")
                else:
                    logger.debug(f"🎭 Слайд #{i}: глобальный макет '{current_layout_name}'")
                
                slide_layout = self._find_layout(prs, current_layout_name)

                if not slide_layout:
                    available = [layout.name for layout in prs.slide_layouts]
                    logger.error(f"❌ Макет '{current_layout_name}' не найден. Доступные: {available}")
                    raise ValueError(
                        f"Макет '{current_layout_name}' не найден в шаблоне. "
                        f"Доступные макеты: {available}"
                    )

                self._add_slide(prs, slide_layout, slide_cfg, i)
                logger.debug(f"✅ Слайд {i} '{slide_cfg.title}' создан успешно")
            except Exception as e:
                error_msg = f"Ошибка при создании слайда {i} ('{slide_cfg.title}'): {e}"
                self._errors.append(error_msg)
                logger.error(f"❌ {error_msg}", exc_info=True)

        # Шаг 4: Вывод итогов
        total_slides = len(config.slides)
        successful_slides = total_slides - len(self._errors)
        
        if self._errors:
            logger.warning(f"⚠️ Завершено с {len(self._errors)} ошибками из {total_slides} слайдов")
            for err in self._errors:
                logger.error(f"  - {err}")
        else:
            logger.info(f"✅ Презентация успешно собрана")

        logger.info(f"📊 Создано слайдов: {successful_slides}/{total_slides}")
        return prs

    def save(self, prs: Presentation, output_path: Path) -> None:
        """
        Сохраняет презентацию в файл.

        Args:
            prs: Объект презентации для сохранения.
            output_path: Путь для сохранения файла.

        Raises:
            IOError: Если не удалось сохранить файл.
        """
        try:
            logger.debug(f"🔧 Сохранение презентации: {output_path}")
            prs.save(str(output_path))
            logger.info(f"✅ Презентация сохранена: {output_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения презентации: {e}", exc_info=True)
            raise IOError(f"Ошибка сохранения презентации: {e}")

    def get_errors(self) -> list:
        """
        Возвращает список ошибок, накопленных в процессе сборки.

        Returns:
            Список строк с описаниями ошибок.
        """
        return self._errors.copy()

    def _add_slide(
        self, prs: Presentation, layout, cfg: BaseSlideConfig, number: int
    ) -> None:
        """
        Добавляет один слайд в презентацию.

        Args:
            prs: Объект презентации.
            layout: Макет слайда из шаблона.
            cfg: Конфигурация слайда (BaseSlideConfig или его подклассы).
            number: Номер слайда (для отображения).
        """
        logger.info(f"📄 Обработка слайда #{number}: '{cfg.title}' (Layout: {layout.name})")
        logger.debug(f"🔍 Тип конфига: {type(cfg).__name__}, изображений: {len(cfg.images) if cfg.images else 0}, аудио: {bool(cfg.audio)}")
        
        # Создание слайда
        slide = prs.slides.add_slide(layout)
        logger.debug(f"🔧 Слайд создан, ID: {slide.slide_id}")

        # Workaround для PowerPoint 2013
        _ = slide.notes_slide

        # Определяем, используется ли TitleLayout
        is_title_layout = isinstance(cfg, YouTubeTitleSlideConfig)

        # Выбираем правильные индексы в зависимости от типа макета
        if is_title_layout:
            idx_title = PLACEHOLDER_TITLE_LAYOUT_TITLE_IDX
            idx_slide_num = PLACEHOLDER_TITLE_LAYOUT_SLIDE_NUM_IDX
        else:
            idx_title = self.idx_title
            idx_slide_num = self.idx_slide_num

        # 1. Заголовок
        try:
            title_ph = slide.shapes.placeholders[idx_title]
            title_ph.text_frame.text = cfg.title
            logger.debug(f"🔧 Title установлен в placeholder idx={idx_title}")
        except KeyError:
            logger.error(f"❌ Заполнитель заголовка idx={idx_title} не найден")
            raise KeyError(f"Заполнитель заголовка с индексом {idx_title} не найден")

        # 2. Дополнительные поля для YouTubeTitleSlideConfig
        if is_title_layout:
            logger.debug("🔧 Обработка YouTube-титульника")
            self._set_youtube_title_fields(slide, cfg)

        # 3. Номер слайда
        try:
            num_ph = slide.shapes.placeholders[idx_slide_num]
            num_ph.text_frame.text = str(number)
            logger.debug(f"🔧 Номер слайда {number} установлен в placeholder idx={idx_slide_num}")
        except KeyError:
            logger.debug(f"🔍 Заполнитель номера idx={idx_slide_num} не найден (не критично)")

        # 4. Заметки докладчика
        logger.debug(f"📝 Загрузка заметок: {cfg.notes_source}")
        notes_text = self.loader.load_notes(cfg.notes_source)
        clean_notes = clean_markdown_for_notes(notes_text)
        slide.notes_slide.notes_text_frame.text = clean_notes
        logger.debug(f"🔧 Заметки добавлены: {len(clean_notes)} символов")

        # 5. Изображения
        logger.debug(f"� Размещение изображений: {len(cfg.images) if cfg.images else 0}")
        self._place_images(slide, cfg)

        # 6. Аудио (если указано)
        if cfg.audio:
            logger.debug(f"🔍 Добавление аудио: {cfg.audio}")
            self._place_audio(slide, cfg.audio)

    def _set_youtube_title_fields(self, slide, cfg: YouTubeTitleSlideConfig) -> None:
        """
        Устанавливает специфичные поля для YouTubeTitleSlideConfig.

        Args:
            slide: Объект слайда.
            cfg: Конфигурация титульного слайда YouTube.

        Note:
            Индексы заполнителей для TitleLayout в youtube_base.pptx:
            - idx=10: title (основной заголовок)
            - idx=12: slide_number (номер слайда)
            - idx=13: subtitle (подзаголовок/описание серии)
        """
        logger.debug(f"🔧 YouTube поля: subtitle='{cfg.subtitle}', series_number={cfg.series_number}")
        
        # Subtitle (placeholder idx=13 в TitleLayout)
        try:
            subtitle_ph = slide.shapes.placeholders[
                PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX
            ]
            subtitle_ph.text_frame.text = cfg.subtitle
            logger.debug(f"🔧 Subtitle установлен в placeholder idx={PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX}")
        except KeyError as e:
            logger.warning(f"⚠️ Заполнитель subtitle idx={PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX} не найден: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка при заполнении subtitle: {e}", exc_info=True)

        # Series number - пока нет заполнителя в шаблоне
        if cfg.series_number:
            logger.debug(f"🔍 Series number '{cfg.series_number}' не добавлен (нет заполнителя)")

    def _place_images(self, slide, cfg: BaseSlideConfig) -> None:
        """
        Размещает изображения на слайде согласно макету.

        Args:
            slide: Объект слайда.
            cfg: Конфигурация слайда.
        """
        if not cfg.images:
            logger.debug("🔍 Нет изображений для размещения")
            return  # Нет изображений - пропускаем

        logger.info(f"🖼️ Размещение изображений для слайда: '{cfg.title}'")
        
        # Получаем чертёж макета
        # Для YouTubeTitleSlideConfig используем фиксированный макет title_youtube
        if isinstance(cfg, YouTubeTitleSlideConfig):
            layout_type = "title_youtube"
            logger.debug("🔍 YouTube титульник -> макет 'title_youtube'")
        else:
            layout_type = cfg.layout_type
            logger.debug(f"🔍 Используем макет из конфига: '{layout_type}'")

        try:
            blueprint = self.layouts.get(layout_type)
            logger.debug(f"🔍 Чертеж макета '{layout_type}': требуется {blueprint.required_images} изображений")
        except KeyError:
            logger.error(f"❌ Макет '{layout_type}' не зарегистрирован. Доступные: {self.layouts.list_all()}")
            raise KeyError(
                f"Макет '{layout_type}' не зарегистрирован. "
                f"Доступные: {self.layouts.list_all()}"
            )

        # Проверка количества изображений
        if len(cfg.images) < blueprint.required_images:
            logger.warning(
                f"⚠️ Ожидалось {blueprint.required_images} изображений, предоставлено {len(cfg.images)}"
            )

        # Размещение каждого изображения
        for i, img_path_str in enumerate(cfg.images):
            if i >= len(blueprint.placements):
                # Больше изображений, чем размещений - игнорируем лишние
                logger.warning(f"⚠️ Изображение #{i + 1} '{img_path_str}' игнорируется (нет размещения в макете)")
                break

            try:
                logger.debug(f"📍 Размещение изображения: {img_path_str}")
                
                # Разрешение пути к изображению
                img_path = self.loader.resolve_image(img_path_str)

                # Автоматическая конвертация WebP → PNG (in-memory)
                original_path = img_path
                image_source = img_path  # По умолчанию используем путь к файлу

                if img_path.suffix.lower() == ".webp":
                    try:
                        # convert_webp_to_png теперь возвращает BytesIO
                        image_source = convert_webp_to_png(img_path)
                        logger.debug(f"🔄 WebP сконвертирован в памяти: {original_path.name}")
                    except Exception as e:
                        error_msg = f"Ошибка конвертации WebP {img_path_str}: {e}"
                        self._errors.append(error_msg)
                        logger.error(f"❌ {error_msg}", exc_info=True)
                        continue

                # Получение параметров размещения
                placement = blueprint.placements[i]
                placement_dict = placement.to_dict()
                
                logger.debug(
                    f"📏 Чертеж: left={placement_dict['left']}, top={placement_dict['top']}, "
                    f"max_width={placement_dict['max_width']}, max_height={placement_dict['max_height']}"
                )

                # Умное масштабирование (для BytesIO используем исходный путь)
                dimensions_source = (
                    original_path if img_path.suffix.lower() == ".webp" else img_path
                )
                width, height = calculate_smart_dimensions(
                    dimensions_source,
                    placement_dict["max_width"],
                    placement_dict["max_height"],
                )

                # Конвертация в единицы python-pptx
                left_cm = Cm(placement_dict["left"])
                top_cm = Cm(placement_dict["top"])
                width_cm = Cm(width) if width is not None else None
                height_cm = Cm(height) if height is not None else None
                
                width_str = f"{width:.2f}" if width is not None else "auto"
                height_str = f"{height:.2f}" if height is not None else "auto"
                logger.debug(
                    f"📐 Вычислено (см): left={placement_dict['left']:.2f}, top={placement_dict['top']:.2f}, "
                    f"w={width_str}, h={height_str}"
                )
                
                # EMU для детального логирования
                emu_left = int(left_cm)
                emu_top = int(top_cm)
                emu_width = int(width_cm) if width_cm else None
                emu_height = int(height_cm) if height_cm else None
                
                logger.debug(
                    f"🎯 Финальные EMU: left={emu_left}, top={emu_top}, "
                    f"width={emu_width or 'auto'}, height={emu_height or 'auto'}"
                )

                # Добавление изображения на слайд
                # python-pptx поддерживает как пути (str/Path), так и потоки (BytesIO)
                if isinstance(image_source, Path):
                    slide.shapes.add_picture(
                        str(image_source),
                        left_cm,
                        top_cm,
                        width=width_cm,
                        height=height_cm,
                    )
                else:
                    # BytesIO передаём напрямую
                    slide.shapes.add_picture(
                        image_source, left_cm, top_cm, width=width_cm, height=height_cm
                    )

            except FileNotFoundError:
                # Изображение не найдено - добавляем в ошибки, но продолжаем
                error_msg = f"Изображение не найдено: {img_path_str}"
                self._errors.append(error_msg)
                logger.warning(f"⚠️ {error_msg}")

            except Exception as e:
                # Другая ошибка при добавлении изображения
                error_msg = f"Ошибка добавления изображения {img_path_str}: {e}"
                self._errors.append(error_msg)
                logger.error(f"❌ {error_msg}", exc_info=True)

    def _place_audio(self, slide, audio_path_str: str) -> None:
        """
        Размещает аудиофайл на слайде используя workaround через add_movie.

        Args:
            slide: Объект слайда.
            audio_path_str: Путь к аудиофайлу (строка).

        Note:
            python-pptx не имеет нативного метода add_audio, поэтому используется
            add_movie с mime_type='video/mp4'. PowerPoint корректно распознает аудио
            при открытии. Объект скрывается за пределами видимой области слайда.
        """
        logger.info(f"🎵 Добавление медиа: {audio_path_str}")
        
        try:
            # Разрешаем путь к аудиофайлу
            audio_path = self.loader.resolve_audio(audio_path_str)
            
            logger.debug(f"🔗 Вставка медиа-блоба: {audio_path.name}, MIME: video/mp4")
            logger.debug("🔧 Применен audio workaround: Координаты left=0cm, top=-10cm")

            # Используем add_movie workaround
            # Геометрия: минимальный размер (1x1 см), вынесен за пределы слайда
            slide.shapes.add_movie(
                str(audio_path),
                left=Cm(0),
                top=Cm(-10),  # Скрыт за верхней границей слайда
                width=Cm(1),
                height=Cm(1),
                mime_type="video/mp4",  # Критично для прохождения валидации библиотеки
            )

            logger.debug("🔧 Аудио добавлено успешно")

        except FileNotFoundError:
            error_msg = f"Аудиофайл не найден: {audio_path_str}"
            self._errors.append(error_msg)
            logger.warning(f"⚠️ Медиа-файл не найден: {audio_path_str}, продолжаем без него")

        except Exception as e:
            # Не блокируем генерацию слайда, если аудио не вставилось
            error_msg = f"Ошибка добавления аудио {audio_path_str}: {e}"
            self._errors.append(error_msg)
            logger.error(f"❌ {error_msg}", exc_info=True)

    @staticmethod
    def _find_layout(prs: Presentation, layout_name: str):
        """
        Ищет макет по имени в шаблоне.

        Args:
            prs: Объект презентации.
            layout_name: Имя макета для поиска.

        Returns:
            Объект макета или None, если не найден.
        """
        logger.debug(f"🔍 Поиск макета '{layout_name}' в мастере...")
        
        for layout in prs.slide_layouts:
            if layout.name == layout_name:
                logger.debug(f"🔧 Макет '{layout_name}' найден")
                return layout
        
        logger.warning(f"⚠️ Макет '{layout_name}' не найден в шаблоне")
        return None

```

## `core/template_analyzer.py`

```py
"""
Анализатор шаблонов PowerPoint.

Этот модуль позволяет анализировать структуру .pptx шаблонов
для определения индексов заполнителей и параметров макетов.
"""

import logging
from pathlib import Path
from pptx import Presentation

logger = logging.getLogger(__name__)


def analyze_template(template_path: Path, layout_name: str = "VideoLayout") -> None:
    """
    Анализирует шаблон PPTX и выводит информацию о макетах и заполнителях.

    Args:
        template_path: Путь к файлу шаблона .pptx.
        layout_name: Имя макета для детального анализа (опционально).

    Example:
        >>> analyze_template(Path("template.pptx"), "VideoLayout")
    """
    logger.info(f"🔍 Анализ шаблона: {template_path}")
    logger.debug(f"🔍 Целевой макет для детального анализа: '{layout_name}'")
    
    try:
        prs = Presentation(str(template_path))
        logger.debug("🔧 Шаблон успешно загружен")
    except FileNotFoundError:
        logger.error(f"❌ Файл не найден: {template_path}")
        return
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки шаблона: {e}", exc_info=True)
        return

    # Вывод всех доступных макетов
    logger.info(f"📋 Найдено макетов: {len(prs.slide_layouts)}")
    
    for i, layout in enumerate(prs.slide_layouts):
        logger.debug(f"🔍 Макет #{i + 1}: '{layout.name}'")

    # Поиск нужного макета
    target_layout = None
    for layout in prs.slide_layouts:
        if layout.name == layout_name:
            target_layout = layout
            break

    if not target_layout:
        logger.warning(f"⚠️ Макет '{layout_name}' не найден в шаблоне")
        return

    # Детальный анализ макета
    logger.debug(f"🔍 Начинаем детальный анализ макета '{layout_name}'")

    placeholders = target_layout.placeholders

    if not placeholders:
        logger.debug(f"🔍 Макет '{layout_name}' не содержит заполнителей")
        return

    logger.debug(f"📋 Найдено заполнителей: {len(placeholders)}")

    for ph in placeholders:
        logger.debug(
            f"🔧 Заполнитель: idx={ph.placeholder_format.idx}, "
            f"type={ph.placeholder_format.type}, name='{ph.name}'"
        )

        # Попытка получить текст (если есть)
        try:
            if hasattr(ph, "text_frame") and ph.text_frame:
                sample_text = (
                    ph.text_frame.text[:50] if ph.text_frame.text else "(пусто)"
                )
                logger.debug(f"🔧 Текст заполнителя: {sample_text}")
        except Exception:
            pass

    logger.info("✅ Анализ шаблона завершён успешно")


def list_layouts(template_path: Path) -> None:
    """
    Выводит простой список макетов в шаблоне.

    Args:
        template_path: Путь к файлу шаблона.
    """
    logger.info(f"📋 Запрошен список макетов для: {template_path}")
    
    try:
        prs = Presentation(str(template_path))
        logger.debug(f"🔧 Шаблон успешно загружен: {len(prs.slide_layouts)} макетов")
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки шаблона: {e}", exc_info=True)
        return

    for i, layout in enumerate(prs.slide_layouts, 1):
        logger.debug(f"🔍 Макет #{i}: '{layout.name}'")
    
    logger.info(f"✅ Список макетов выведен: {len(prs.slide_layouts)} шт.")

```

## `doc/layouts/single_tall.md`

```md
# single_tall — Одно высокое изображение

> 📐 **Макет:** 1 изображение вертикальной ориентации  
> 🎯 **Рекомендуемые пропорции:** 9:16 или близкие

## Описание

Размещает одно высокое изображение в центре слайда. Идеально подходит для:

- Скриншотов мобильных приложений
- Вертикальных списков и меню
- Портретных фотографий
- Высоких диаграмм и графиков

## Технические характеристики

- **Требуемое количество изображений:** 1
- **Координаты:** left=10.46 см, top=2.96 см
- **Максимальные размеры:** 11.2 см × 15.2 см
- **Пропорции области:** ~3:4 (вертикальная)

## Пример использования

### JSON конфигурация

```json
{
  "layout_type": "single_tall",
  "title": "Список расширений Python",
  "notes_source": "Здесь показан полный список доступных расширений для Python в Visual Studio Code.",
  "images": [
    "images/python_extensions_list.png"
  ]
}
```

### Результат

```
┌─────────────────────────────────────────┐
│  Список расширений Python               │
├─────────────────────────────────────────┤
│                                         │
│         ┌─────────────┐                 │
│         │             │                 │
│         │   [Высокое  │                 │
│         │ изображение]│                 │
│         │             │                 │
│         │             │                 │
│         └─────────────┘                 │
│                                         │
└─────────────────────────────────────────┘
```

## Советы по использованию

✅ **Рекомендуется:**

- Использовать изображения с соотношением сторон ~9:16 или 3:4
- Минимальное разрешение: 1080×1920 пикселей (для мобильных скриншотов)
- Формат: PNG (для скриншотов UI)

❌ **Не рекомендуется:**

- Горизонтальные изображения (используйте `single_wide`)
- Слишком широкие изображения (будут с большими боковыми отступами)
- Квадратные изображения (неэффективное использование пространства)

## Связанные макеты

- Для горизонтальных изображений → `single_wide`
- Для двух вертикальных изображений → `two_tall_row`

```

## `doc/layouts/single_wide.md`

```md
# single_wide — Одно широкое изображение

> 📐 **Макет:** 1 изображение горизонтальной ориентации  
> 🎯 **Рекомендуемые пропорции:** 16:9 или близкие

## Описание

Размещает одно широкое изображение в центре слайда. Идеально подходит для:

- Горизонтальных скриншотов интерфейсов
- Широких диаграмм и схем
- Панорамных фотографий
- Визуализации данных в альбомной ориентации

## Технические характеристики

- **Требуемое количество изображений:** 1
- **Координаты:** left=10.2 см, top=4.2 см
- **Максимальные размеры:** 20.0 см × 10.0 см
- **Пропорции области:** ~2:1 (широкая)

## Пример использования

### JSON конфигурация

```json
{
  "layout_type": "single_wide",
  "title": "Страница загрузки VS Code",
  "notes_source": "На этом скриншоте показана главная страница загрузки Visual Studio Code с вариантами для Windows, Linux и Mac.",
  "images": [
    "images/vscode_download_page.png"
  ]
}
```

### Результат

```
┌─────────────────────────────────────────┐
│  Страница загрузки VS Code              │
├─────────────────────────────────────────┤
│                                         │
│     ┌───────────────────────────┐       │
│     │                           │       │
│     │   [Широкое изображение]   │       │
│     │                           │       │
│     └───────────────────────────┘       │
│                                         │
└─────────────────────────────────────────┘
```

## Советы по использованию

✅ **Рекомендуется:**

- Использовать изображения с соотношением сторон ~16:9
- Минимальное разрешение: 1920×1080 пикселей
- Формат: PNG (для скриншотов), JPEG (для фото)

❌ **Не рекомендуется:**

- Вертикальные изображения (используйте `single_tall`)
- Слишком узкие изображения (будут с большими отступами)
- Изображения низкого разрешения (будут размытыми при растяжении)

## Связанные макеты

- Для вертикальных изображений → `single_tall`
- Для двух широких изображений → `two_stack`

```

## `doc/layouts/three_stack.md`

```md
# three_stack — Три изображения вертикально

> 📐 **Макет:** 3 изображения друг под другом  
> 🎯 **Рекомендуемые пропорции:** 16:9 или близкие (широкие)

## Описание

Размещает три широких изображения друг под другом вертикально. Идеально подходит для:

- Пошаговых инструкций из трёх шагов
- Сравнения трёх вариантов интерфейса
- Показа эволюции дизайна (версия 1 → 2 → 3)
- Демонстрации трёх последовательных экранов

## Технические характеристики

- **Требуемое количество изображений:** 3
- **Координаты:**
  - Верхнее: left=10.16 см, top=3.0 см
  - Среднее: left=10.16 см, top=7.5 см
  - Нижнее: left=10.16 см, top=12.0 см
- **Максимальные размеры:** 18.4 см × 4.0 см (каждое)
- **Пропорции областей:** ~4.6:1 (очень широкие)

## Пример использования

### JSON конфигурация

```json
{
  "layout_type": "three_stack",
  "title": "Три шага установки VS Code",
  "notes_source": "Пошаговая инструкция:\n- Шаг 1: Скачивание установщика\n- Шаг 2: Установка расширений\n- Шаг 3: Финальная настройка",
  "images": [
    "images/step1_download.png",
    "images/step2_extensions.png",
    "images/step3_config.png"
  ]
}
```

### Результат

```
┌─────────────────────────────────────────┐
│  Три шага установки VS Code             │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   [Изображение 1]               │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   [Изображение 2]               │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   [Изображение 3]               │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

## Советы по использованию

✅ **Рекомендуется:**

- Использовать изображения **одинаковой ширины** для визуальной гармонии
- Обрезать изображения горизонтально (убрать лишнюю высоту)
- Идеально для последовательных шагов с номерами

❌ **Не рекомендуется:**

- Вертикальные высокие изображения (будут слишком сжаты)
- Изображения с большим количеством мелких деталей (станут нечитаемыми)
- Слишком разные по стилю изображения

## Связанные макеты

- Для 1 широкого изображения → `single_wide`
- Для 2 изображений вертикально → `two_stack`

```

## `doc/layouts/two_stack.md`

```md
# two_stack — Два изображения вертикально

> 📐 **Макет:** 2 изображения друг под другом  
> 🎯 **Рекомендуемые пропорции:** 16:9 для каждого (широкие)

## Описание

Размещает два широких изображения друг под другом. Идеально подходит для:

- Сравнения «до и после»
- Последовательных шагов в инструкции
- Демонстрации двух версий интерфейса
- Показа разных состояний системы

## Технические характеристики

- **Требуемое количество изображений:** 2
- **Координаты:**
  - Верхнее: left=10.16 см, top=3.47 см
  - Нижнее: left=10.16 см, top=11.0 см
- **Максимальные размеры:**
  - Верхнее: 18.4 см × 3.91 см
  - Нижнее: 18.07 см × 4.58 см
- **Пропорции областей:** широкие (~5:1 и ~4:1)

## Пример использования

### JSON конфигурация

```json
{
  "layout_type": "two_stack",
  "title": "Расширения Cline и Excalidraw",
  "notes_source": "На верхнем скриншоте — карточка Cline, на нижнем — Excalidraw.",
  "images": [
    "images/cline_extension.png",
    "images/excalidraw_extension.png"
  ]
}
```

### Результат

```
┌─────────────────────────────────────────┐
│  Расширения Cline и Excalidraw          │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   [Верхнее изображение]         │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   [Нижнее изображение]          │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

## Советы по использованию

✅ **Рекомендуется:**

- Использовать изображения одинаковой ширины для визуальной гармонии
- Обрезать изображения до нужной области (убрать лишние поля)
- Использовать для сравнения или последовательности

❌ **Не рекомендуется:**

- Вертикальные высокие изображения (будут сильно сжаты)
- Изображения разной стилистики (нарушит единообразие)
- Более 2 изображений (используйте `three_stack`)

## Связанные макеты

- Для 1 широкого изображения → `single_wide`
- Для 3 изображений вертикально → `three_stack`
- Для 2 изображений горизонтально → `two_tall_row`

```

## `doc/layouts/two_tall_row.md`

```md
# two_tall_row — Два высоких изображения рядом

> 📐 **Макет:** 2 изображения горизонтально  
> 🎯 **Рекомендуемые пропорции:** 9:16 или 3:4 для каждого (вертикальные)

## Описание

Размещает два высоких изображения рядом друг с другом. Идеально подходит для:

- Сравнения двух мобильных приложений
- Показа двух вертикальных списков
- Демонстрации вариантов интерфейса side-by-side
- Сравнения «старое vs новое» для мобильных UI

## Технические характеристики

- **Требуемое количество изображений:** 2
- **Координаты:**
  - Левое: left=10.2 см, top=2.4 см
  - Правое: left=21.89 см, top=2.4 см
- **Максимальные размеры:** 10.5 см × 14.5 см (каждое)
- **Пропорции областей:** ~3:4 (вертикальные)

## Пример использования

### JSON конфигурация

```json
{
  "layout_type": "two_tall_row",
  "title": "Сравнение версий мобильного приложения",
  "notes_source": "Слева — старая версия интерфейса, справа — новая с обновлённым дизайном.",
  "images": [
    "images/mobile_old_version.png",
    "images/mobile_new_version.png"
  ]
}
```

### Результат

```
┌─────────────────────────────────────────┐
│  Сравнение версий мобильного приложения │
├─────────────────────────────────────────┤
│                                         │
│   ┌──────────┐      ┌──────────┐        │
│   │          │      │          │        │
│   │  [Левое  │      │ [Правое  │        │
│   │   изобр.]│      │  изобр.] │        │
│   │          │      │          │        │
│   │          │      │          │        │
│   └──────────┘      └──────────┘        │
│                                         │
└─────────────────────────────────────────┘
```

## Советы по использованию

✅ **Рекомендуется:**

- Использовать изображения одинаковой высоты
- Идеально для скриншотов мобильных приложений (9:16)
- Обрезать изображения до одинаковых размеров для симметрии

❌ **Не рекомендуется:**

- Горизонтальные широкие изображения (используйте `two_stack`)
- Изображения сильно разной высоты (нарушит баланс)
- Более 2 изображений (нет места)

## Связанные макеты

- Для 1 вертикального изображения → `single_tall`
- Для 2 изображений вертикально → `two_stack`

```

## `doc/LOGGING.md`

```md
# 📊 Система логирования

## Обзор

Presentation Builder использует централизованную систему логирования на базе стандартной библиотеки Python `logging`. Система настроена для удобной отладки как во время разработки, так и при работе на продакшене.

## Структура логов

### 🎯 Три потока логирования

1. **Console (stdout)** — то, что видит пользователь
   - Уровень: `INFO` (или `DEBUG` с флагом `--verbose`)
   - Формат: упрощенный для читаемости

2. **logs/app.log** — полная история работы приложения
   - Уровень: `DEBUG` (все детали)
   - Формат: полный с временем, модулем, строкой кода
   - Ротация: 5 МБ × 3 бэкапа

3. **logs/error.log** — только ошибки
   - Уровень: `ERROR` и `CRITICAL`
   - Формат: полный с Stack Trace
   - Ротация: 5 МБ × 3 бэкапа

## Использование

### Флаг --verbose

```bash
# Обычный режим (INFO в консоли)
python main.py generate --config slides.json

# Детальный режим (DEBUG в консоли)
python main.py generate --config slides.json --verbose
```

### В коде модуля

```python
import logging

# Получаем логгер для текущего модуля
logger = logging.getLogger(__name__)

# Используем разные уровни
logger.debug("🔍 Детальная информация для отладки")
logger.info("✅ Важное событие для пользователя")
logger.warning("⚠️ Предупреждение о потенциальной проблеме")
logger.error("❌ Ошибка, но работа продолжается", exc_info=True)
logger.critical("💥 Критическая ошибка, работа невозможна", exc_info=True)
```

## Уровни логирования

### 🔍 DEBUG (только в app.log)

**Когда использовать**: детали внутренней работы, значения переменных, промежуточные вычисления.

**Примеры**:

- Сырые данные из JSON перед парсингом
- Резолюция путей к файлам (input → absolute)
- Размеры изображений и координаты размещения
- Математика масштабирования (ratio, dimensions в пикселях/см/EMU)
- Дампы конфигураций и промежуточных объектов

### ✅ INFO (в app.log + console)

**Когда использовать**: важные события для пользователя, прогресс работы.

**Примеры**:

- Начало/завершение основных операций
- "Обработка слайда #1"
- "Презентация сохранена: output.pptx"
- "Создано слайдов: 5"

### ⚠️ WARNING (в app.log + console)

**Когда использовать**: проблемы, не останавливающие работу.

**Примеры**:

- Не найдена опциональная картинка (слайд создан, но пустой)
- Макет не найден, используется дефолтный
- Отсутствует аудио-файл (продолжаем без звука)

### ❌ ERROR (в app.log + error.log + console)

**Когда использовать**: ошибки, прерывающие текущую операцию.

**Примеры**:

- Файл конфигурации не найден
- Битый JSON
- Ошибка валидации структуры
- Ошибка конвертации изображения

**Важно**: всегда используйте `exc_info=True` для записи Stack Trace!

```python
try:
    # ... код
except Exception as e:
    logger.error(f"❌ Ошибка: {e}", exc_info=True)
    raise
```

### 💥 CRITICAL (в app.log + error.log + console)

**Когда использовать**: неперехваченные исключения, крах программы.

**Примеры**:

- Uncaught exception в main()
- Отсутствие критических библиотек (python-pptx, Pillow)
- Невозможность создать презентацию

## Система эмодзи (единообразная)

### По уровням

- **DEBUG**: 🔍 🔧 📐 🎯 📊 🗂️ 📏 📍 🔗
- **INFO**: ✅ ▶️ 📥 🖼️ 🎵 🚀 📄 📊 📋
- **WARNING**: ⚠️
- **ERROR**: ❌
- **CRITICAL**: 💥

### По типам операций

- **Файлы**: 📂 📄 🗂️ 📥
- **Обработка**: 🔄 ✂️ 🧹 ✨
- **Презентации**: 🚀 📊 🎨 🎭 📄
- **Изображения**: 🖼️ 📐 📏 🎯
- **Медиа**: 🎵 🎧 🔗
- **MCP**: 🤖 📚 📋
- **Заметки**: 📝

## Карта логирования по модулям

### core/presentation_builder.py

```python
# Инициализация
logger.debug("⚙️ Инициализация PresentationBuilder: idx_title=0, idx_slide_num=1")

# Начало сборки
logger.info("🚀 Начало сборки презентации из шаблона: template.pptx")
logger.debug("📂 Полный путь к шаблону: C:/templates/template.pptx")

# Обработка слайдов
logger.info('📄 Обработка слайда #1: "Заголовок" (Layout: TitleLayout)')
logger.debug('🎭 Выбор макета: Config="TitleLayout" vs Global="Content". Итог: "TitleLayout"')

# Размещение изображений
logger.info('🖼️ Размещение изображений для слайда: "Заголовок"')
logger.debug("📍 Размещение изображения: photo.jpg")
logger.debug("📏 Чертеж: left=1.0, top=2.0, width=10.0, height=5.0")
logger.debug("📐 Вычислено (см): left=1.00, top=2.00, w=10.00, h=5.00")
logger.debug("🎯 Финальные EMU: left=360000, top=720000, width=3600000, height=1800000")

# Завершение
logger.info("✅ Презентация сохранена: output.pptx")
logger.info("📊 Создано слайдов: 5")
```

### core/image_processor.py

```python
logger.debug("🖼️ Информация об изображении: Format=JPEG, Mode=RGB, Size=1920x1080")
logger.debug("🔄 Конвертация WebP в PNG: image.webp")
logger.debug("📊 Метрики конвертации: WebP 150000 байт -> PNG 450000 байт, Mode: RGB")
logger.debug("📐 Исходные размеры: 1920x1080, Ограничитель: 1000x1000")
logger.debug("🎯 Логика масштабирования: Ratio исх=1.78, цель=1.00, Выбор: Fit by WIDTH")
logger.debug("✂️ Вычисленные размеры: 1000x562")
```

### io_handlers/config_loader.py

```python
logger.info("📥 Загрузка конфигурации: slides.json")
logger.debug("🔍 Сырые данные (первые 500 символов): {\"template\": ...}")
logger.debug("🔧 Применение дефолтных значений: template_path=template.pptx, layout=Content")
logger.debug("🔍 Сырые данные слайда: {'title': 'Slide 1', 'images': [...]}")
logger.info("✅ Конфигурация загружена успешно")
logger.error("❌ Не удалось загрузить конфигурацию: invalid JSON", exc_info=True)
```

### io_handlers/path_resolver.py

```python
logger.debug('🗂️ Резолюция пути: Input="images/photo.jpg" | Base="C:/project" | Result="C:/project/images/photo.jpg"')
```

### io_handlers/resource_loader.py

```python
logger.debug("🔍 Файл найден: photo.jpg, Размер: 150000 байт")
logger.debug("📝 Загрузка заметок из notes.md")
logger.warning("⚠️ Не найден файл заметок: missing.md")
```

### cli/commands.py

```python
logger.info("▶️ Запущена команда generate. Config: slides.json, Output: output.pptx")
logger.info("✅ Генерация завершена успешно")
logger.critical("💥 Критическая ошибка при генерации: File not found", exc_info=True)
```

### mcp_server.py

```python
logger.info("🤖 MCP запрос: generate_presentation")
logger.debug("📋 Конфигурация от агента (первые 1000 символов): {\"slides\": ...}")
logger.debug("🔍 Проверка существования файла: C:/config.json")
logger.info("✅ MCP ответ: Успех")
logger.error("❌ MCP ответ: Ошибка - File not found")
logger.info("📚 MCP запрос: get_layout_documentation(single_wide)")
```

## Отладка проблем

### Картинка отображается не там/не того размера

1. Открыть `logs/app.log`
2. Найти строку с нужным слайдом: `📄 Обработка слайда #3`
3. Смотреть блок с `📍 Размещение изображения`
4. Проверить:
   - Чертеж (blueprint) — исходные координаты из макета
   - Вычисленные размеры в см
   - Финальные EMU (которые идут в python-pptx)

### Файл не найден

1. Открыть `logs/app.log`
2. Найти `🗂️ Резолюция пути` для проблемного файла
3. Проверить:
   - Input (что пришло из JSON)
   - Base (от какой папки резолвим)
   - Result (итоговый абсолютный путь)

### Ошибка валидации JSON

1. Открыть `logs/app.log`
2. Найти `📥 Загрузка конфигурации`
3. Посмотреть сырые данные (raw payload)
4. Проверить `🔍 Сырые данные слайда` для каждого слайда

### Агент (MCP) возвращает ошибку

1. Открыть `logs/app.log`
2. Найти `🤖 MCP запрос`
3. Посмотреть `📋 Конфигурация от агента`
4. Проверить путь в `🔍 Проверка существования файла`
5. Если есть `❌ MCP ответ: Ошибка` — смотреть error.log для Stack Trace

## Формат файлов логов

### Формат строки

```
[2025-11-20 14:30:15] DEBUG    core.presentation_builder:145 - 📍 Размещение изображения: photo.jpg
```

**Поля**:

- `[2025-11-20 14:30:15]` — timestamp
- `DEBUG` — уровень (8 символов, выравнивание)
- `core.presentation_builder` — имя модуля (из `__name__`)
- `145` — номер строки кода
- `📍 Размещение изображения: photo.jpg` — сообщение

### Ротация файлов

Когда `app.log` достигает 5 МБ:

```
logs/
  app.log         # текущий
  app.log.1       # предыдущий
  app.log.2       # еще старше
  app.log.3       # самый старый (потом удаляется)
```

То же самое для `error.log`.

## Кодировка

Все файлы логов используют **UTF-8** для корректного отображения:

- Русских букв
- Эмодзи
- Специальных символов в путях (например, китайские/японские имена файлов)

## Best Practices

### ✅ Хорошо

```python
logger.debug(f"📐 Исходные размеры: {img_w}x{img_h}, Ограничитель: {max_w}x{max_h}")
logger.info(f"✅ Презентация сохранена: {output_path}")
logger.error(f"❌ Не удалось загрузить: {path}", exc_info=True)
```

### ❌ Плохо

```python
logger.debug("Image dimensions")  # Нет значений!
logger.info("Done")  # Что именно done?
logger.error("Error occurred")  # Нет exc_info, Stack Trace потерян!
```

### Правило "Параноидального DEBUG"

В DEBUG логах должно быть **все**, что нужно для отладки без запуска дебаггера:

- Точные пути к файлам (resolved)
- Размеры картинок (пиксели, см, EMU)
- Промежуточные вычисления (ratios, scaling logic)
- Дампы структур данных (первые N символов)

### Когда использовать exc_info=True

**Всегда** при ERROR и CRITICAL, если есть исключение:

```python
try:
    # ... опасный код
except Exception as e:
    logger.error(f"❌ Ошибка: {e}", exc_info=True)
    raise  # или обработать иначе
```

Это запишет полный Stack Trace в `error.log` и `app.log`.

## Интеграция с тестами

При запуске pytest логи автоматически перехватываются. Для просмотра:

```bash
# Показать логи только упавших тестов
pytest -v

# Показать все логи (включая успешные тесты)
pytest -v -s

# Показать только WARNING и выше
pytest --log-cli-level=WARNING
```

## Troubleshooting

### Логи не создаются

- Проверить права на запись в папку проекта
- Убедиться, что `setup_logging()` вызван в `main.py`

### Русские буквы отображаются как "????"

- Проверить, что редактор открывает файл в UTF-8
- В Windows может потребоваться `chcp 65001` перед запуском

### Логи слишком большие

- Система автоматически ротирует (5 МБ × 3 бэкапа)
- Старые файлы удаляются сами
- Всего максимум ~15 МБ на app.log + ~15 МБ на error.log

### Хочу отключить логи в файл

В `core/logger.py` закомментировать хендлеры для app.log и error.log.
Останется только console.

---

**Документация актуальна на**: 2025-11-20  
**Версия системы логирования**: 1.0

```

## `doc/mcp-tools-guide.md`

```md
# Полное руководство по созданию MCP инструментов

<div align="center">

# 🛠️ Создание MCP инструментов от А до Я

**Полное руководство для AI-агентов по созданию локальных MCP серверов**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io)

</div>

---

## 📋 Оглавление

- [Введение](#введение)
- [Быстрый старт](#быстрый-старт)
- [Архитектура MCP сервера](#архитектура-mcp-сервера)
- [Создание инструментов](#создание-инструментов)
- [Структурированные ответы](#структурированные-ответы)
- [Обработка ошибок](#обработка-ошибок)
- [Конфигурация и ключи API](#конфигурация-и-ключи-api)
- [Лучшие практики](#лучшие-практики)
- [Примеры](#примеры)

---

## 🎯 Введение

### 📚 ID библиотеки в Context7

**`/modelcontextprotocol/python-sdk`** - используйте этот ID для поиска документации по MCP Python SDK в Context7

### Что такое MCP?

**Model Context Protocol (MCP)** - это открытый протокол для создания инструментов, которые могут использоваться AI-агентами. MCP серверы предоставляют инструменты и ресурсы, которые агенты могут вызывать для выполнения различных задач.

### Зачем создавать MCP инструменты?

- **Локальное выполнение** - инструменты работают на вашей машине
- **Конфиденциальность** - данные не уходят в облако
- **Гибкость** - можно создавать любые инструменты под свои нужды
- **Стандартизация** - единый интерфейс для всех инструментов

### Ключевые концепции

- **Сервер** - программа, предоставляющая инструменты
- **Инструмент** - функция, которую может вызывать AI-агент
- **Ресурс** - данные, к которым может обращаться сервер
- **Промпт** - шаблоны для генерации контента

---

## 🚀 Быстрый старт

### Минимальный MCP сервер

Создайте файл `simple_server.py`:

```python
"""Простой MCP сервер с одним инструментом."""

from mcp.server.fastmcp import FastMCP

# Создаем сервер с именем
mcp = FastMCP("Simple Server")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Сложить два числа и вернуть результат.
    
    Args:
        a: Первое число для сложения
        b: Второе число для сложения
        
    Returns:
        Сумма двух чисел
    """
    return a + b

if __name__ == "__main__":
    mcp.run()
```

### Запуск сервера

```bash
python simple_server.py
```

### Использование в Cline

После запуска сервера, Cline сможет использовать инструмент `add_numbers`:

```
"Пожалуйста, сложи 5 и 7 используя инструмент add_numbers"
```

---

## 🏗️ Архитектура MCP сервера

### Базовая структура проекта

```
my-mcp-server/
├── server.py              # Главный файл сервера
├── config.py              # Конфигурация
├── requirements.txt       # Зависимости
├── tools/                 # Инструменты
│   ├── __init__.py
│   └── calculator.py      # Пример инструмента
├── models/                # Модели данных
│   ├── __init__.py
│   └── responses.py       # Структурированные ответы
└── utils/                 # Утилиты
    ├── __init__.py
    └── api_client.py      # Клиенты API
```

### Основные компоненты

1. **server.py** - точка входа, регистрация инструментов
2. **tools/** - модули с инструментами
3. **models/** - Pydantic модели для структурированных ответов
4. **utils/** - общие утилиты и клиенты API

---

## 🛠️ Создание инструментов

### Базовый инструмент

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Example Server")

@mcp.tool()
def greet_user(name: str, style: str = "friendly") -> str:
    """Поприветствовать пользователя в указанном стиле.
    
    Args:
        name: Имя пользователя для приветствия
        style: Стиль приветствия (friendly, formal, casual)
        
    Returns:
        Приветственное сообщение
    """
    styles = {
        "friendly": f"Привет, {name}! Как дела?",
        "formal": f"Здравствуйте, {name}.",
        "casual": f"Йо, {name}! Что нового?"
    }
    return styles.get(style, f"Привет, {name}!")
```

### Ключевые моменты

- **Докстринг** становится подсказкой для AI-агентов
- **Типы параметров** автоматически создают схему
- **Значения по умолчанию** делают параметры опциональными

---

## 📊 Структурированные ответы

### Использование Pydantic моделей

```python
from pydantic import BaseModel, Field
from typing import Optional

class WeatherInfo(BaseModel):
    """Информация о погоде."""
    
    temperature: float = Field(..., description="Температура в градусах Цельсия")
    condition: str = Field(..., description="Погодные условия")
    humidity: Optional[float] = Field(None, description="Влажность в процентах")
    wind_speed: Optional[float] = Field(None, description="Скорость ветра в м/с")

@mcp.tool()
def get_weather(city: str) -> WeatherInfo:
    """Получить информацию о погоде в указанном городе.
    
    Args:
        city: Название города для получения погоды
        
    Returns:
        Структурированная информация о погоде
    """
    # Здесь может быть вызов API погоды
    return WeatherInfo(
        temperature=22.5,
        condition="солнечно",
        humidity=45.0,
        wind_speed=3.2
    )
```

### Преимущества структурированных ответов

- **Автоматическая валидация** данных
- **Четкая документация** полей через Field(description=...)
- **Согласованность** формата ответов
- **Легкая интеграция** с другими системами

---

## ⚠️ Обработка ошибок

### Структурированные ошибки

```python
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    """Структурированный ответ об ошибке."""
    
    error: str = Field(..., description="Описание ошибки")
    details: Optional[str] = Field(None, description="Детали ошибки")
    suggestion: Optional[str] = Field(None, description="Предложение по исправлению")

@mcp.tool()
def divide_numbers(a: float, b: float) -> float | ErrorResponse:
    """Разделить два числа.
    
    Args:
        a: Делимое
        b: Делитель
        
    Returns:
        Результат деления или информация об ошибке
    """
    try:
        if b == 0:
            return ErrorResponse(
                error="Деление на ноль",
                details="Параметр b не может быть равен 0",
                suggestion="Используйте ненулевое значение для b"
            )
        return a / b
    except Exception as e:
        return ErrorResponse(
            error="Ошибка при делении",
            details=str(e)
        )
```

### Лучшие практики обработки ошибок

- **Всегда возвращайте структурированные ошибки**
- **Предоставляйте полезные детали** для отладки
- **Включайте предложения** по исправлению
- **Логируйте ошибки** для диагностики

---

## 🔑 Конфигурация и ключи API

### Гибкая загрузка API ключей

```python
"""config.py - Управление конфигурацией и API ключами"""

import os
from typing import Optional

def get_api_key(api_name: str) -> str:
    """Получить API ключ с приоритетом переменных окружения.
    
    Args:
        api_name: Название API (например, 'OPENAI', 'GEMINI')
        
    Returns:
        API ключ
        
    Raises:
        ValueError: Если ключ не найден
    """
    env_var_name = f"{api_name}_API_KEY"
    api_key = os.getenv(env_var_name)
    
    if not api_key:
        raise ValueError(
            f"Ключ {env_var_name} не найден. "
            f"Установите его как переменную окружения или "
            f"передайте через конфигурацию клиента MCP."
        )
    
    return api_key

# Пример использования в инструменте
@mcp.tool()
def analyze_with_openai(text: str) -> str:
    """Проанализировать текст с помощью OpenAI API.
    
    Args:
        text: Текст для анализа
        
    Returns:
        Результат анализа
    """
    try:
        api_key = get_api_key("OPENAI")
        # Используем api_key для вызова OpenAI API
        return f"Анализ завершен для текста: {text}"
    except ValueError as e:
        return f"Ошибка конфигурации: {e}"
```

### Передача ключей через клиент

Ключи передаются через переменные окружения в конфигурации клиента:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-openai-key-here",
        "GEMINI_API_KEY": "your-gemini-key-here"
      }
    }
  }
}
```

---

## 📝 Лучшие практики

### Документация инструментов

**Хороший докстринг:**

```python
@mcp.tool()
def calculate_bmi(weight: float, height: float) -> dict:
    """Рассчитать индекс массы тела (BMI).
    
    BMI рассчитывается как вес в килограммах, деленный на 
    квадрат роста в метрах.
    
    Args:
        weight: Вес в килограммах (должен быть > 0)
        height: Рост в метрах (должен быть > 0)
        
    Returns:
        Словарь с результатами:
        - bmi: Рассчитанный индекс массы тела
        - category: Категория BMI (недостаточный, нормальный, избыточный)
        - description: Описание категории
        
    Raises:
        ValueError: Если вес или рост не положительные числа
    """
    if weight <= 0 or height <= 0:
        raise ValueError("Вес и рост должны быть положительными числами")
    
    bmi = weight / (height ** 2)
    
    if bmi < 18.5:
        category = "недостаточный вес"
    elif bmi < 25:
        category = "нормальный вес"
    elif bmi < 30:
        category = "избыточный вес"
    else:
        category = "ожирение"
    
    return {
        "bmi": round(bmi, 2),
        "category": category,
        "description": f"Ваш BMI {bmi:.1f} соответствует категории '{category}'"
    }
```

### Ключевые элементы хорошей документации

1. **Четкое описание** что делает инструмент
2. **Подробные параметры** с типами и ограничениями
3. **Пример возвращаемых данных**
4. **Возможные ошибки** и их причины
5. **Формулы или алгоритмы** если применимо

---

## 🎯 Пример: Полный MCP сервер

### Структура проекта

```
weather-mcp/
├── server.py
├── config.py
├── requirements.txt
├── tools/
│   ├── __init__.py
│   └── weather_tools.py
└── models/
    ├── __init__.py
    └── weather_models.py
```

### server.py

```python
"""MCP сервер для работы с погодой."""

from mcp.server.fastmcp import FastMCP
from tools.weather_tools import get_current_weather, get_weather_forecast

mcp = FastMCP("Weather Server")

# Регистрируем инструменты
mcp.tool()(get_current_weather)
mcp.tool()(get_weather_forecast)

if __name__ == "__main__":
    mcp.run()
```

### models/weather_models.py

```python
"""Модели данных для погодного сервера."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CurrentWeather(BaseModel):
    """Текущая погода."""
    
    temperature: float = Field(..., description="Температура в °C")
    condition: str = Field(..., description="Погодные условия")
    humidity: float = Field(..., description="Влажность в %")
    wind_speed: float = Field(..., description="Скорость ветра в м/с")
    feels_like: float = Field(..., description="Ощущаемая температура")

class ForecastDay(BaseModel):
    """Прогноз погоды на день."""
    
    date: str = Field(..., description="Дата прогноза")
    max_temp: float = Field(..., description="Максимальная температура")
    min_temp: float = Field(..., description="Минимальная температура")
    condition: str = Field(..., description="Погодные условия")

class WeatherForecast(BaseModel):
    """Прогноз погоды на несколько дней."""
    
    location: str = Field(..., description="Местоположение")
    current: CurrentWeather = Field(..., description="Текущая погода")
    forecast: List[ForecastDay] = Field(..., description="Прогноз на дни")
```

### tools/weather_tools.py

```python
"""Инструменты для работы с погодой."""

from models.weather_models import CurrentWeather, WeatherForecast, ForecastDay

def get_current_weather(city: str) -> CurrentWeather:
    """Получить текущую погоду для указанного города.
    
    Args:
        city: Название города на английском (например, "London", "New York")
        
    Returns:
        Текущая погода в городе
        
    Example:
        get_current_weather("London") -> CurrentWeather with London weather
    """
    # Здесь будет вызов реального API погоды
    # Для примера возвращаем фиктивные данные
    return CurrentWeather(
        temperature=15.5,
        condition="облачно",
        humidity=65.0,
        wind_speed=4.2,
        feels_like=14.0
    )

def get_weather_forecast(city: str, days: int = 3) -> WeatherForecast:
    """Получить прогноз погоды на указанное количество дней.
    
    Args:
        city: Название города
        days: Количество дней для прогноза (1-7)
        
    Returns:
        Прогноз погоды на указанное количество дней
    """
    if days < 1 or days > 7:
        raise ValueError("Количество дней должно быть от 1 до 7")
    
    current = get_current_weather(city)
    forecast_days = []
    
    for i in range(days):
        forecast_days.append(ForecastDay(
            date=f"2024-01-{10 + i}",
            max_temp=current.temperature + i,
            min_temp=current.temperature - 2 - i,
            condition="переменная облачность"
        ))
    
    return WeatherForecast(
        location=city,
        current=current,
        forecast=forecast_days
    )
```

### requirements.txt

```
mcp>=1.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

---

## 🔧 Реальный Workflow агента с инструментами

### Как работает взаимодействие

**Пользователь → Агент → Инструмент → Агент → Пользователь**

1. **Пользователь**: "Я думаю что я хочу в Лондон. Узнай какая там будет погода?"
2. **Агент**:
   - Анализирует запрос пользователя
   - Видит доступный инструмент `get_weather`
   - Читает документацию инструмента: требуется параметр `city`
   - Формирует запрос к инструменту: `get_weather("London")`
3. **Инструмент**: Возвращает структурированные данные о погоде
4. **Агент**:
   - Получает данные от инструмента
   - Формирует естественный ответ на основе полученных данных
   - Отвечает пользователю: "В Лондоне сейчас 15°C, облачно, влажность 65%"

### Пример реального диалога

```
Пользователь: "Мне нужно проанализировать это изображение с кошкой"

Агент: "Я вижу у вас есть изображение. Использую инструмент analyze_image для анализа."

[Агент вызывает analyze_image с абсолютным путем к файлу]

Агент: "На изображении я вижу рыжую кошку породы мейн-кун, 
        сидящую на подоконнике. Она смотрит в окно, 
        за которым видны деревья и голубое небо. 
        Шерсть кошки пушистая, глаза зеленые..."
```

---

## ⚙️ Правильная конфигурация Cline для MCP серверов

### Реальная конфигурация нашего проекта

```json
{
  "mcpServers": {
    "gemini-media-mcp": {
      "autoApprove": [
        "analyze_image",
        "analyze_audio"
      ],
      "disabled": false,
      "timeout": 300,
      "type": "stdio",
      "command": "C:/PY/gemini-media-mcp/.venv/Scripts/python.exe",
      "args": [
        "C:/PY/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

### Пример для погодного сервера с API ключом

```json
{
  "mcpServers": {
    "weather-server": {
      "autoApprove": [
        "get_current_weather",
        "get_weather_forecast"
      ],
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "C:/projects/weather-mcp/.venv/Scripts/python.exe",
      "args": [
        "C:/projects/weather-mcp/server.py"
      ],
      "env": {
        "WEATHER_API_KEY": "your-weather-api-key-here",
        "OPENWEATHER_API_KEY": "your-openweather-key-here"
      }
    }
  }
}
```

### Ключевые параметры конфигурации

- **`command`**: Исполняемый файл (python, node, docker и т.д.)
- **`args`**: Аргументы командной строки для запуска сервера
- **`env`**: Переменные окружения, которые парсятся в MCP сервере через `os.getenv()`
- **`autoApprove`**: Инструменты, которые не требуют подтверждения пользователя
- **`timeout`**: Таймаут выполнения инструментов в секундах
- **`type`**: Всегда `"stdio"` для локальных серверов

---

## 🔑 Как MCP сервер парсит конфигурацию

### Реальный код из нашего config.py

```python
import os

def get_api_key() -> str:
    """
    Получает API-ключ Gemini из переменных окружения или файла .env.

    Приоритет:
    1. Переменная окружения `GEMINI_API_KEY` (из конфигурации Cline)
    2. Файл `.env` в корневом каталоге проекта (для локальной разработки)

    Returns:
        str: Найденный API-ключ.

    Raises:
        ValueError: Если API-ключ не найден ни в одном из источников.
    """
    # 1. Проверяем переменные окружения (высший приоритет)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    # 2. Пытаемся загрузить из .env (для удобства локальной разработки)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            return api_key
    except ImportError:
        pass

    # 3. Если ключ не найден, вызываем ошибку
    raise ValueError(
        "Ключ GEMINI_API_KEY не найден. "
        "Пожалуйста, установите его как переменную окружения или "
        "передайте через конфигурацию клиента MCP."
    )

# API ключ загружается при импорте модуля
GEMINI_API_KEY = get_api_key()
```

### Пример для погодного сервера

```python
"""config.py для погодного сервера"""

import os

def get_weather_api_key() -> str:
    """Получить API ключ для погодного сервиса."""
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise ValueError(
            "Ключ WEATHER_API_KEY не найден. "
            "Установите его в конфигурации Cline в разделе env."
        )
    return api_key

def get_openweather_key() -> str:
    """Получить API ключ для OpenWeather."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError(
            "Ключ OPENWEATHER_API_KEY не найден. "
            "Установите его в конфигурации Cline."
        )
    return api_key

# Загружаем ключи при импорте
WEATHER_API_KEY = get_weather_api_key()
OPENWEATHER_API_KEY = get_openweather_key()
```

### Использование в инструментах

```python
@mcp.tool()
def get_current_weather(city: str) -> CurrentWeather:
    """Получить текущую погоду для указанного города.
    
    Args:
        city: Название города на английском
        
    Returns:
        Текущая погода в городе
    """
    # Используем API ключ из конфигурации
    api_key = WEATHER_API_KEY
    
    # Здесь реальный вызов погодного API
    response = requests.get(
        f"https://api.weather.com/v1/current?city={city}&key={api_key}"
    )
    
    # Обрабатываем ответ и возвращаем структурированные данные
    return CurrentWeather(
        temperature=response.json()["temp"],
        condition=response.json()["condition"],
        humidity=response.json()["humidity"],
        wind_speed=response.json()["wind_speed"]
    )
```

---

## 🔍 Реальные примеры из нашего проекта

### Анализ изображений (tools/image_analyzer.py)

```python
def analyze_image(
    image_path: str,
    user_prompt: str = "",
    model_name: str | None = None,
    system_instruction_name: str = "default",
    system_instruction_override: str | None = None,
    system_instruction_file_path: str | None = None,
) -> ImageAnalysisResponse | ErrorResponse:
    """Analyze images using Google Gemini API.

    Returns structured result with alt-text and detailed analysis.
    Supported formats: JPEG, PNG, GIF, WEBP, HEIC, HEIF

    Args:
        image_path: Absolute path to the image file on local machine.
        user_prompt: Custom analysis request (optional).
        model_name: The Gemini model to use (e.g., "gemini-1.5-flash").
                    Defaults to the one specified in config.py.
        system_instruction_name: Name of predefined system instruction.
        system_instruction_override: Custom system instruction (overrides system_instruction_name).
        system_instruction_file_path: Path to file with system instruction (highest priority).

    Returns:
        Structured analysis response with alt-text and detailed analysis.
        
    Raises:
        ValueError: If image is invalid or system instruction not found.
        FileNotFoundError: If image file or system instruction file not found.
        IOError: If error reading files.
    """
```

### Ключевые особенности нашего подхода

1. **Абсолютные пути** - все пути должны быть абсолютными
2. **Гибкие системные инструкции** - поддержка файлов, переопределений и предустановок
3. **Структурированные ошибки** - всегда возвращаем ErrorResponse при проблемах
4. **Валидация моделей** - проверка поддерживаемых моделей Gemini

---

## 🚫 Важные ограничения и особенности

### Абсолютные пути обязательны

```python
# ❌ НЕПРАВИЛЬНО - относительный путь
image_path = "images/photo.jpg"

# ✅ ПРАВИЛЬНО - абсолютный путь
image_path = "C:/Users/user/Documents/images/photo.jpg"
```

### Передача файлов через stdin/stdout

Наш сервер работает через **stdio transport**, что означает:

- **Нет HTTP сервера** - все через стандартные потоки ввода/вывода
- **Локальное выполнение** - инструменты запускаются на вашей машине
- **Быстрая коммуникация** - минимальные накладные расходы

### Конфигурация через переменные окружения

```python
# config.py - наш подход к загрузке API ключей
def get_api_key() -> str:
    """Получает API-ключ Gemini из переменных окружения или файла .env."""
    
    # 1. Переменные окружения (высший приоритет)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    # 2. Файл .env (для удобства разработки)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            return api_key
    except ImportError:
        pass

    # 3. Ошибка если ключ не найден
    raise ValueError("Ключ GEMINI_API_KEY не найден")
```

---

## 🎯 Шаблон для быстрого старта

### Минимальный рабочий сервер

```python
"""minimal_mcp_server.py - Шаблон для быстрого создания MCP сервера"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional

# Создаем сервер
mcp = FastMCP("My Tools Server")

# Модель для структурированного ответа
class ToolResult(BaseModel):
    """Результат выполнения инструмента."""
    success: bool = Field(..., description="Успешно ли выполнена операция")
    result: str = Field(..., description="Результат операции")
    details: Optional[str] = Field(None, description="Детали выполнения")

@mcp.tool()
def process_data(input_data: str, method: str = "default") -> ToolResult:
    """Обработать входные данные указанным методом.
    
    Args:
        input_data: Данные для обработки
        method: Метод обработки (default, advanced, simple)
        
    Returns:
        Результат обработки данных
    """
    try:
        if method == "default":
            result = f"Обработано: {input_data}"
        elif method == "advanced":
            result = f"Расширенная обработка: {input_data.upper()}"
        elif method == "simple":
            result = f"Простая обработка: {input_data.lower()}"
        else:
            return ToolResult(
                success=False,
                result="",
                details=f"Неизвестный метод: {method}"
            )
            
        return ToolResult(
            success=True,
            result=result,
            details=f"Обработка завершена методом '{method}'"
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            result="",
            details=f"Ошибка обработки: {str(e)}"
        )

if __name__ == "__main__":
    mcp.run()
```

### requirements.txt для шаблона

```
mcp>=1.0.0
pydantic>=2.0.0
```

---

## 🎯 Практический пример: Presentation Builder

### Simple Tool Pattern в действии

Рассмотрим реальный пример MCP сервера для автоматизации создания PowerPoint презентаций.

#### Задача

Создать инструмент, который:

- ✅ Принимает путь к JSON конфигурации
- ✅ Создаёт PowerPoint презентацию
- ✅ Возвращает результат агенту

#### Реализация

```python
#!/usr/bin/env python3
"""MCP Server для Presentation Builder"""

from mcp.server.fastmcp import FastMCP
from pathlib import Path
from models import LayoutRegistry
from io_handlers import PathResolver, ConfigLoader, ResourceLoader
from core import PresentationBuilder
from config import register_default_layouts

# Создаём MCP сервер
mcp = FastMCP("Presentation Builder")

@mcp.tool()
def generate_presentation(config_path: str) -> str:
    """Создать PowerPoint презентацию из JSON конфигурации.
    
    Args:
        config_path: Абсолютный путь к JSON файлу с конфигурацией слайдов.
                    JSON должен содержать:
                    - template_path: путь к PPTX шаблону
                    - layout_name: имя макета из шаблона
                    - output_path: куда сохранить результат
                    - slides: массив слайдов с title, notes_source, images, layout_type
        
    Returns:
        Сообщение о результате создания презентации
        
    Example:
        generate_presentation("C:/projects/my_slides.json")
        -> "✅ Презентация создана: C:/projects/output.pptx"
    """
    try:
        # Валидация входных данных
        config_file = Path(config_path)
        if not config_file.exists():
            return f"❌ Ошибка: Файл не найден: {config_path}"
        
        if config_file.suffix.lower() != '.json':
            return f"❌ Ошибка: Требуется JSON файл"
        
        # Загрузка конфигурации
        config = ConfigLoader.load(config_file)
        
        if not config.slides:
            return "❌ Ошибка: В конфигурации нет слайдов"
        
        # Настройка компонентов
        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)
        registry = LayoutRegistry()
        register_default_layouts(registry)
        
        # Создание презентации
        builder = PresentationBuilder(registry, loader, verbose=False)
        template_path = resolver.resolve(config.template_path)
        
        if not template_path.exists():
            return f"❌ Ошибка: Шаблон не найден: {template_path}"
        
        prs = builder.build(config, template_path)
        
        if prs is None:
            return "❌ Критическая ошибка при сборке презентации"
        
        # Сохранение результата
        output_path = resolver.resolve(config.output_path)
        builder.save(prs, output_path)
        
        # Проверка ошибок
        errors = builder.get_errors()
        
        # Формирование ответа
        result = (
            f"✅ Презентация успешно создана!\n"
            f"📁 Файл: {output_path}\n"
            f"📊 Создано слайдов: {len(config.slides)}\n"
            f"🎨 Макет: {config.layout_name}"
        )
        
        if errors:
            result += f"\n⚠️  Некритичных ошибок: {len(errors)}"
        
        return result
        
    except FileNotFoundError as e:
        return f"❌ Файл не найден: {e}"
    except ValueError as e:
        return f"❌ Ошибка конфигурации: {e}"
    except PermissionError as e:
        return f"❌ Нет прав доступа: {e}"
    except Exception as e:
        return f"❌ Неожиданная ошибка: {type(e).__name__}: {e}"

if __name__ == "__main__":
    mcp.run()
```

#### Пример JSON конфигурации

```json
{
  "template_path": "c:\\PY\\presentation_mcp\\template.pptx",
  "layout_name": "VideoLayout",
  "output_path": "c:\\PY\\presentation_mcp\\output.pptx",
  "slides": [
    {
      "layout_type": "single_wide",
      "title": "Качаем VS Code",
      "notes_source": "Сейчас мы должны скачать VS Code\n- Пункт 1\n- Пункт 2",
      "images": [
        "c:\\PY\\presentation_mcp\\images\\screenshot1.png"
      ]
    },
    {
      "layout_type": "two_stack",
      "title": "Два изображения",
      "notes_source": "Сравнение двух вариантов",
      "images": [
        "c:\\PY\\presentation_mcp\\images\\image1.png",
        "c:\\PY\\presentation_mcp\\images\\image2.png"
      ]
    }
  ]
}
```

### Конфигурация для Cline

Добавьте в файл `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "presentation-builder": {
      "autoApprove": [
        "generate_presentation"
      ],
      "disabled": false,
      "timeout": 120,
      "type": "stdio",
      "command": "C:/PY/presentation_mcp/.venv/Scripts/python.exe",
      "args": [
        "C:/PY/presentation_mcp/mcp_server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

**Важные моменты:**

1. **`autoApprove`** - список инструментов, которые можно выполнять без подтверждения
2. **`timeout`** - таймаут в секундах (120 для создания презентаций)
3. **`command`** - **абсолютный путь** к Python из виртуального окружения
4. **`args`** - **абсолютный путь** к MCP серверу
5. **`env`** - переменные окружения для корректной работы с UTF-8

### Использование с AI-агентом

После настройки вы можете просить агента:

```
Пользователь: "Создай презентацию из конфига C:/PY/presentation_mcp/doc/samples/slides_config.json"

Агент: "Использую инструмент generate_presentation..."

[Вызывает generate_presentation("C:/PY/presentation_mcp/doc/samples/slides_config.json")]

Агент: "✅ Презентация успешно создана!
       📁 Файл: C:/PY/presentation_mcp/output.pptx
       📊 Создано слайдов: 4
       🎨 Макет: VideoLayout"
```

### Ключевые преимущества этого подхода

✅ **Один инструмент = одна функция** - просто и понятно  
✅ **Абсолютные пути** - нет проблем с рабочей директорией  
✅ **Понятные ошибки** - агент получает информативные сообщения  
✅ **Использование существующего кода** - не нужно переписывать логику  
✅ **Быстрая разработка** - от CLI до MCP за 30 минут  

### Проверка работоспособности

Протестируйте MCP сервер напрямую:

```bash
# Активируйте виртуальное окружение
C:/PY/presentation_mcp/.venv/Scripts/activate

# Запустите сервер
python mcp_server.py

# Сервер должен запуститься без ошибок и ждать команд от клиента
```

Если видите ошибки импорта - проверьте установку зависимостей:

```bash
pip install -r requirements.txt
```

---

## 🔧 Интеграция с существующими проектами

### Добавление MCP инструментов в существующий код

Если у вас уже есть Python проект, добавить MCP инструменты очень просто:

```python
# existing_project.py
from mcp.server.fastmcp import FastMCP

# Ваш существующий код
def existing_function(data: str) -> dict:
    """Существующая функция."""
    return {"processed": data.upper(), "length": len(data)}

# Создаем MCP сервер
mcp = FastMCP("Existing Project Tools")

# Обертываем существующую функцию в MCP инструмент
@mcp.tool()
def process_with_existing(data: str) -> dict:
    """Обработать данные существующей функцией.
    
    Args:
        data: Входные данные для обработки
        
    Returns:
        Результат обработки
    """
    return existing_function(data)

if __name__ == "__main__":
    mcp.run()
```

---

## 🎉 Заключение

### Ключевые выводы для AI-агентов

1. **MCP инструменты просты в создании** - достаточно декоратора `@mcp.tool()`
2. **Докстринг критически важен** - это подсказка для AI-агентов
3. **Структурированные ответы** улучшают качество взаимодействия
4. **Абсолютные пути обязательны** для работы с файлами
5. **Локальное выполнение** обеспечивает конфиденциальность
6. **Гибкая конфигурация** через переменные окружения

### Что делать дальше?

1. **Начните с простого** - создайте минимальный сервер с 1-2 инструментами
2. **Используйте структурированные ответы** - Pydantic модели ваш друг
3. **Тестируйте с Cline** - убедитесь что инструменты работают корректно
4. **Расширяйте постепенно** - добавляйте новые инструменты по мере необходимости

### Помните

> "Лучший MCP инструмент - это тот, который решает конкретную задачу просто и надежно. Не усложняйте без необходимости."

---

<div align="center">

## 🚀 Готовы создавать свои MCP инструменты?

**Начните с нашего шаблона и создайте свой первый инструмент за 5 минут!**

[📚 Документация MCP](https://modelcontextprotocol.io) •
[🐍 Python SDK](https://github.com/modelcontextprotocol/python-sdk) •
[💡 Примеры](https://github.com/modelcontextprotocol/servers)

</div>

```

## `doc/MCP_USAGE.md`

```md
# MCP Server для Presentation Builder

## 🤖 Использование с AI-агентами (MCP)

Presentation Builder поддерживает **Model Context Protocol (MCP)**, что позволяет AI-агентам (например, Cline) автоматически создавать презентации через простой инструмент.

### Быстрый старт с MCP

#### 1. Убедитесь что установлен MCP SDK

```bash
pip install mcp
```

#### 2. Запустите MCP сервер

```bash
python mcp_server.py
```

#### 3. Настройте Cline

Добавьте в файл `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "presentation-builder": {
      "autoApprove": [
        "generate_presentation"
      ],
      "disabled": false,
      "timeout": 120,
      "type": "stdio",
      "command": "C:/PY/presentation_mcp/.venv/Scripts/python.exe",
      "args": [
        "C:/PY/presentation_mcp/mcp_server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

**Важно:** Замените пути на ваши абсолютные пути!

#### 4. Используйте с AI-агентом

Теперь вы можете просто попросить агента:

```
"Создай презентацию из файла C:/PY/presentation_mcp/doc/samples/slides_config.json"
```

Агент автоматически вызовет инструмент `generate_presentation` и создаст презентацию.

### Доступные инструменты

#### `generate_presentation`

Создаёт PowerPoint презентацию из JSON конфигурации.

**Параметры:**

- `config_path` (string, обязательно) - Абсолютный путь к JSON файлу с конфигурацией

**Возвращает:**

- Сообщение о результате с путём к созданному файлу

**Пример использования:**

```python
generate_presentation("C:/projects/my_presentation/slides_config.json")
```

**Ответ:**

```
✅ Презентация успешно создана!
📁 Файл: C:/projects/my_presentation/output.pptx
📊 Создано слайдов: 4
🎨 Макет: VideoLayout
```

### Преимущества MCP интеграции

✅ **Автоматизация** - AI создаёт презентации без вашего участия  
✅ **Простота** - один инструмент, понятный интерфейс  
✅ **Локальное выполнение** - данные не уходят в облако  
✅ **Гибкость** - можно изменять логику работы инструмента  

### Устранение проблем

#### Ошибка импорта MCP

```bash
pip install --upgrade mcp
```

#### Сервер не запускается

Проверьте что все зависимости установлены:

```bash
pip install -r requirements.txt
```

#### Cline не видит инструмент

1. Проверьте что пути в `cline_mcp_settings.json` **абсолютные**
2. Убедитесь что MCP сервер запускается без ошибок
3. Перезапустите Cline

#### Ошибка "Шаблон не найден"

MCP сервер ищет шаблоны в **своей директории**, а не в директории JSON файла.

**Решение:**

- **Относительные пути** (например `template.pptx`) ищутся в **директории MCP сервера**
- **Абсолютные пути** используются как есть
- Положите шаблоны в `C:/PY/presentation_mcp/` (где лежит `mcp_server.py`)

**Примеры:**

```json
{
  "template_path": "template.pptx",  // → C:/PY/presentation_mcp/template.pptx
  "output_path": "output.pptx",      // → C:/PY/presentation_mcp/output.pptx
  "slides": [
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Контентный слайд",
      "images": ["image.png"]
    }
  ]
}

// Для титульных слайдов YouTube:
{
  "template_path": "templates/youtube_base.pptx",
  "output_path": "youtube_presentation.pptx",
  "layout_name": "VideoLayout",
  "slides": [
    {
      "slide_type": "title_youtube",
      "layout_type": "title_youtube",
      "layout_name": "TitleLayout",
      "title": "Название канала",
      "subtitle": "Описание серии",
      "series_number": "Часть 1",
      "images": ["logo.png"]
    }
  ]
}
```

**Важно:** Изображения разрешаются через `PathResolver` относительно JSON файла!

#### Ошибка "unsupported image format WEBP"

python-pptx изначально не поддерживает WebP формат.

**Решение:**

Presentation Builder **автоматически конвертирует WebP → PNG** при обработке слайдов.

- ✅ WebP изображения поддерживаются (автоматическая конвертация)
- ✅ Поддерживаемые форматы: **BMP, GIF, JPEG, PNG, TIFF, WMF, WebP**
- ✅ Временные PNG файлы автоматически удаляются после вставки в презентацию
- ⚠️ Требуется установленный Pillow (уже в requirements.txt)

### Дополнительная документация

Подробное руководство по созданию MCP инструментов: [`mcp-tools-guide.md`](mcp-tools-guide.md)

```

## `doc/overview.md`

```md
# Presentation Builder — Автоматизация создания PowerPoint презентаций

## Назначение

Presentation Builder — это система автоматической генерации PowerPoint презентаций из JSON-конфигурации.
Создавайте слайды с изображениями и заметками докладчика автоматически.

## Основные возможности

- ✅ Создание слайдов из JSON-конфигурации
- ✅ Поддержка разных типов слайдов (обычные + титульные YouTube)
- ✅ Переопределение макета PowerPoint на уровне слайда
- ✅ Умное масштабирование изображений с сохранением пропорций
- ✅ 6 готовых макетов размещения изображений
- ✅ Поддержка заметок докладчика из Markdown
- ✅ Автоматическая конвертация WebP в PNG
- ✅ **НОВОЕ!** Добавление аудио (озвучка, музыка) к слайдам

---

## Доступные макеты PowerPoint (layout_name)

В шаблоне `youtube_base.pptx` доступны следующие макеты:

### `TitleLayout` — Титульный слайд

Используется для обложки презентации или YouTube видео.

**Обязательные поля:**

- `slide_type: "title_youtube"`
- `layout_type: "title_youtube"`
- `layout_name: "TitleLayout"`
- `title` — название канала/презентации
- `subtitle` — описание серии (обязательно!)
- `images` — ровно 1 изображение (квадратное, для логотипа)

### `VideoLayout` — Контентный слайд

Используется для обычных слайдов с контентом.

**Обязательные поля:**

- `slide_type: "content"`
- `layout_type` — один из: `single_wide`, `single_tall`, `two_stack`, `two_tall_row`, `three_stack`
- `title` — заголовок слайда
- `images` — от 1 до 3 изображений (в зависимости от layout_type)

---

## Доступные макеты размещения изображений (layout_type)

1. **single_wide** — одно широкое изображение (16:9)
2. **single_tall** — одно высокое изображение (9:16)
3. **two_stack** — два изображения друг под другом
4. **two_tall_row** — два высоких изображения рядом
5. **three_stack** — три изображения вертикально
6. **title_youtube** — титульный слайд YouTube (логотип канала)

---

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Создание конфигурации

```json
{
  "template_path": "templates/youtube_base.pptx",
  "layout_name": "VideoLayout",
  "output_path": "output.pptx",
  "slides": [
    {
      "slide_type": "title_youtube",
      "layout_type": "title_youtube",
      "layout_name": "TitleLayout",
      "title": "Мой YouTube Канал",
      "subtitle": "Python для начинающих",
      "images": ["logo.png"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Заголовок слайда",
      "notes_source": "Текст заметок докладчика",
      "images": ["path/to/image.png"]
    }
  ]
}
```

### 3. Генерация презентации

```bash
python main.py generate config.json
```

## Доступные команды CLI

### `generate` — генерация презентации

```bash
python main.py generate slides.json
python main.py generate slides.json -o output.pptx
python main.py generate slides.json -t custom_template.pptx
```

### `analyze` — анализ структуры шаблона

```bash
python main.py analyze template.pptx
python main.py analyze template.pptx -l CustomLayout
python main.py analyze template.pptx --list
```

### `help` — справка

```bash
python main.py help
```

## Доступные макеты

Система включает 6 предустановленных макетов размещения изображений:

1. **single_wide** — одно широкое изображение (16:9)
2. **single_tall** — одно высокое изображение (9:16)
1. **single_wide** — одно широкое изображение (16:9)
2. **single_tall** — одно высокое изображение (9:16)
3. **two_stack** — два изображения друг под другом
4. **two_tall_row** — два высоких изображения рядом
5. **three_stack** — три изображения вертикально
6. **title_youtube** — титульный слайд YouTube (логотип канала)

Подробное описание каждого макета см. в `doc/layouts/<имя_макета>.md`.

## MCP Server

Проект включает MCP-сервер для интеграции с AI-агентами (Claude, ChatGPT и др.).

### Доступные MCP-инструменты

- `create_presentation` — создание презентации из JSON
- `get_layout_documentation` — получение документации по макетам

### Запуск MCP-сервера

```bash
python mcp_server.py
```

## Структура JSON-конфигурации

### Корневой объект

| Поле | Тип | Описание |
|------|-----|----------|
| `template_path` | string | Путь к файлу шаблона PPTX |
| `layout_name` | string | Имя макета в шаблоне (по умолчанию: VideoLayout) |
| `output_path` | string | Путь к выходному файлу |
| `slides` | array | Массив объектов слайдов |

### Объект слайда

| Поле | Тип | Описание |
|------|-----|----------|
| `slide_type` | string | Тип слайда: `content` (по умолчанию) или `title_youtube` |
| `layout_type` | string | Тип макета размещения изображений (см. выше список) |
| `layout_name` | string | Переопределение макета PowerPoint для конкретного слайда (TitleLayout или VideoLayout) |
| `title` | string | Заголовок слайда |
| `notes_source` | string | Текст заметок или путь к .md файлу |
| `images` | array | Массив путей к изображениям |

**Дополнительные поля для `slide_type: "title_youtube"`:**

| Поле | Тип | Описание |
|------|-----|----------|
| `subtitle` | string | Подзаголовок/описание серии (обязательно) |
| `series_number` | string | Номер части серии (опционально) |

## Умное масштабирование

Система автоматически вычисляет размеры изображений с сохранением пропорций:

- Если изображение **шире** отведённой области → фиксируется ширина
- Если изображение **выше** отведённой области → фиксируется высота
- Изображение **никогда не растягивается** и не искажается

## Поддерживаемые форматы изображений

- ✅ PNG, JPEG, BMP, GIF, TIFF
- ✅ WebP (автоматическая конвертация в PNG)

---

**Дата обновления:** 19 ноября 2025  
**Версия:** 2.0

```

## `doc/REFERENCE.md`

```md
# Руководство по использованию Presentation Builder

## Оглавление

- [Быстрый старт](#быстрый-старт)
- [Использование с AI-агентами (MCP)](#использование-с-ai-агентами-mcp)
- [Конфигурационный файл](#конфигурационный-файл)
- [CLI команды](#cli-команды)
- [Макеты (Layouts)](#макеты-layouts)
- [Пути к файлам](#пути-к-файлам)
- [Markdown заметки](#markdown-заметки)
- [Расширяемость](#расширяемость)

---

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Подготовка файлов

Вам понадобятся:

- **Шаблон PowerPoint** (`template.pptx`) с нужными макетами
- **Конфигурационный JSON** файл с описанием слайдов
- **Изображения** для слайдов
- **Markdown файлы** для заметок (опционально)

### 3. Создание конфигурации

Создайте JSON файл (например, `config.json`):

```json
{
  "template_path": "template.pptx",
  "layout_name": "single_wide",
  "output_path": "result.pptx",
  "slides": [
    {
      "title": "Мой первый слайд",
      "slide_number": "1",
      "notes_source": "notes.md",
      "images": ["photo.jpg"]
    }
  ]
}
```

### 4. Генерация презентации

```bash
python main.py generate --config config.json
```

Готово! Презентация сохранена в `result.pptx`.

---

## Использование с AI-агентами (MCP)

**Presentation Builder** поддерживает **Model Context Protocol (MCP)**, что позволяет AI-агентам автоматически создавать презентации.

### Быстрая настройка MCP

#### 1. Установите MCP SDK (если ещё не установлен)

```bash
pip install mcp
```

#### 2. Настройте Cline

Создайте или отредактируйте файл `cline_mcp_settings.json` (копируйте из примера):

```json
{
  "mcpServers": {
    "presentation-builder": {
      "autoApprove": ["generate_presentation"],
      "disabled": false,
      "timeout": 120,
      "type": "stdio",
      "command": "C:/PY/presentation_mcp/.venv/Scripts/python.exe",
      "args": ["C:/PY/presentation_mcp/mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

**Важно:** Замените пути на ваши абсолютные пути к Python и mcp_server.py!

#### 3. Используйте с агентом

Теперь можно просто попросить AI:

```
"Создай презентацию из файла C:/projects/slides_config.json"
```

Агент автоматически вызовет инструмент `generate_presentation` и создаст презентацию.

### Доступные MCP инструменты

#### `generate_presentation(config_path: str) -> str`

Создаёт PowerPoint презентацию из JSON конфигурации.

**Параметры:**

- `config_path` - абсолютный путь к JSON файлу

**Возвращает:**

- Сообщение о результате с путём к файлу

**Пример:**

```python
generate_presentation("C:/projects/my_slides.json")
# -> "✅ Презентация создана: C:/projects/output.pptx\n📊 Создано слайдов: 5"
```

### Подробная документация по MCP

- **Руководство по использованию:** [`MCP_USAGE.md`](MCP_USAGE.md)
- **Создание MCP инструментов:** [`mcp-tools-guide.md`](mcp-tools-guide.md)

---

## Конфигурационный файл

### Структура JSON

```json
{
  "template_path": "<путь к шаблону PPTX>",
  "layout_name": "<имя макета из template по умолчанию>",
  "output_path": "<путь к выходному файлу>",
  "slides": [
    {
      "slide_type": "<тип слайда: content (default) или title_youtube>",
      "layout_type": "<тип макета: single_wide, two_stack и т.д.>",
      "title": "<заголовок слайда>",
      "notes_source": "<путь к MD файлу или inline текст>",
      "images": ["<путь к изображению 1>", "<путь к изображению 2>"],
      "layout_name": "<опционально: переопределить макет для этого слайда>",
      "audio": "<опционально: путь к аудиофайлу для озвучки>"
    }
  ]
}
```

### Обязательные поля

**На уровне презентации:**

- `template_path` — путь к шаблону PowerPoint
- `layout_name` — имя макета по умолчанию (должен существовать в шаблоне)
- `slides` — массив слайдов

**На уровне слайда:**

- `layout_type` — тип макета размещения изображений (`single_wide`, `single_tall`, `two_stack`, `two_tall_row`, `three_stack`, `title_youtube`)
- `title` — заголовок слайда
- `notes_source` — заметки из MD файла или inline

### Опциональные поля

**На уровне презентации:**

- `output_path` — если не указан, будет `output.pptx`

**На уровне слайда:**

- `slide_type` — тип слайда: `content` (по умолчанию) или `title_youtube`
- `images` — массив путей к изображениям (по умолчанию пусто)
- `layout_name` — **НОВОЕ!** Переопределение макета PowerPoint для конкретного слайда
- `audio` — **НОВОЕ!** Путь к аудиофайлу для озвучки слайда (опционально)

**Дополнительные поля для `slide_type: "title_youtube"`:**

- `subtitle` — подзаголовок/описание серии (обязательное)
- `series_number` — номер части серии (опционально)

### Использование разных макетов в одной презентации

**Новая возможность:** Теперь вы можете использовать разные макеты PowerPoint в одной презентации!

**Пример:** Титульный слайд + контентные слайды

```json
{
  "template_path": "template.pptx",
  "layout_name": "ContentLayout",
  "slides": [
    {
      "layout_type": "single_wide",
      "layout_name": "TitleLayout",
      "title": "Заголовок презентации",
      "notes_source": "Это титульный слайд",
      "images": ["cover.jpg"]
    },
    {
      "layout_type": "single_wide",
      "title": "Слайд 1",
      "notes_source": "Обычный контентный слайд",
      "images": ["content1.jpg"]
    },
    {
      "layout_type": "two_stack",
      "title": "Слайд 2",
      "notes_source": "Еще один контентный слайд",
      "images": ["img1.jpg", "img2.jpg"]
    }
  ]
}
```

**Как это работает:**

1. **Глобальный `layout_name`** (`ContentLayout`) используется для всех слайдов по умолчанию
2. **Первый слайд** переопределяет макет через `"layout_name": "TitleLayout"`
3. **Остальные слайды** используют глобальный `ContentLayout`

**Типичные сценарии:**

- Титульный слайд + контент
- Разделители разделов + контент
- Слайды с разным расположением элементов

### Пример: YouTube презентация с титульным слайдом

```json
{
  "template_path": "templates/youtube_base.pptx",
  "layout_name": "VideoLayout",
  "output_path": "youtube_presentation.pptx",
  "slides": [
    {
      "slide_type": "title_youtube",
      "layout_type": "title_youtube",
      "layout_name": "TitleLayout",
      "title": "Название канала",
      "subtitle": "Python для начинающих",
      "series_number": "Часть 1",
      "notes_source": "Вводный урок по Python",
      "images": ["channel_logo.png"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Основы синтаксиса",
      "notes_source": "notes/lesson1.md",
      "images": ["syntax_example.png"]
    }
  ]
}
```

**Особенности `slide_type: "title_youtube"`:**

- Использует **один шаблон** `youtube_base.pptx` для всех слайдов
- Титульный слайд использует макет `TitleLayout` (переопределяет глобальный)
- Контентные слайды используют макет `VideoLayout` (глобальный по умолчанию)
- Поле `subtitle` заполняет placeholder idx=13 в TitleLayout
- Поле `series_number` выводится в консоль (нет placeholder в шаблоне)
- Изображение на титульном позиционируется в правый квадрат (координаты в `config/settings.py`)

**⚠️ ВАЖНО:** Нельзя использовать несколько файлов шаблонов! Только один файл с несколькими макетами внутри.

### Пример: Презентация с аудио

Теперь вы можете добавлять аудиофайлы (озвучку, музыку) к слайдам:

```json
{
  "template_path": "template.pptx",
  "layout_name": "ContentLayout",
  "output_path": "presentation_with_audio.pptx",
  "slides": [
    {
      "layout_type": "single_wide",
      "title": "Слайд с озвучкой",
      "notes_source": "Этот слайд имеет аудио дорожку",
      "images": ["slide1.jpg"],
      "audio": "voiceovers/slide1.mp3"
    },
    {
      "layout_type": "two_stack",
      "title": "Слайд без аудио",
      "notes_source": "Обычный слайд",
      "images": ["img1.jpg", "img2.jpg"]
    },
    {
      "layout_type": "single_wide",
      "title": "Еще один слайд с озвучкой",
      "notes_source": "Второй слайд с аудио",
      "images": ["slide3.jpg"],
      "audio": "voiceovers/slide3.wav"
    }
  ]
}
```

**Как работает аудио:**

- Поле `audio` опциональное — можно использовать только на некоторых слайдах
- Поддерживаемые форматы: MP3, WAV, M4A и другие аудиоформаты
- Аудио автоматически скрывается за пределами слайда (не видно визуально)
- При воспроизведении презентации аудио можно запустить кликом на слайд
- Путь к аудиофайлу разрешается относительно JSON конфигурации

**Технические детали:**

- Используется workaround через `add_movie` с `mime_type='video/mp4'`
- PowerPoint корректно распознает аудио при открытии файла
- Объект размещается как 1x1 см за верхней границей слайда (top=-10 см)

### Примеры

См. файлы в `doc/samples/`:

- `simple_example.json` — базовый пример с одним изображением
- `multi_image_example.json` — пример с двумя изображениями
- `absolute_paths_example.json` — пример с абсолютными путями
- `audio_example.json` — **НОВОЕ!** пример с аудио озвучкой

---

## CLI команды

### generate — Генерация презентации

```bash
python main.py generate --config <путь к JSON> [--output <файл>] [--verbose]
```

**Параметры:**

- `--config` — путь к JSON конфигурации (обязательный)
- `--output` — путь к выходному файлу (переопределяет значение из JSON)
- `--verbose` — подробный вывод процесса сборки

**Примеры:**

```bash
# Базовая генерация
python main.py generate --config slides.json

# С явным указанием выходного файла
python main.py generate --config slides.json --output presentation.pptx

# С подробным логированием
python main.py generate --config slides.json --verbose
```

### analyze — Анализ шаблона

```bash
python main.py analyze --template <путь к PPTX> [--layout <имя>]
```

**Параметры:**

- `--template` — путь к шаблону PowerPoint (обязательный)
- `--layout` — имя конкретного макета для детального анализа (опционально)

**Примеры:**

```bash
# Список всех макетов в шаблоне
python main.py analyze --template template.pptx

# Детальный анализ конкретного макета
python main.py analyze --template template.pptx --layout "Blank"
```

### help — Справка

```bash
python main.py help
```

Выводит справку по всем доступным командам и их использованию.

---

## Макеты (Layouts)

### Встроенные макеты

Система поставляется с 4 предустановленными макетами:

#### 1. `single_wide` — Одно широкое изображение

- **1 изображение**: горизонтальное размещение (16:9 оптимально)
- Использование: пейзажи, панорамы, широкие диаграммы

#### 2. `single_tall` — Одно высокое изображение

- **1 изображение**: вертикальное размещение (9:16 оптимально)
- Использование: портреты, скриншоты мобильных приложений

#### 3. `two_stack` — Два изображения вертикально

- **2 изображения**: расположены друг над другом
- Использование: сравнение "до/после", этапы процесса

#### 4. `two_tall_row` — Два высоких изображения рядом

- **2 изображения**: два вертикальных изображения в ряд
- Использование: сравнение портретов, скриншоты

### Создание собственных макетов

См. раздел [Расширяемость](#расширяемость).

---

## Пути к файлам

### Относительные пути

По умолчанию все пути в JSON интерпретируются **относительно расположения JSON файла**.

**Пример:**

Структура файлов:

```
project/
  config/
    slides.json          ← JSON файл здесь
  images/
    photo.jpg
  notes/
    slide1.md
  template.pptx
```

Содержимое `slides.json`:

```json
{
  "template_path": "../template.pptx",
  "slides": [
    {
      "notes_source": "../notes/slide1.md",
      "images": ["../images/photo.jpg"]
    }
  ]
}
```

При запуске `python main.py generate --config config/slides.json` все пути будут правильно разрешены относительно `config/`.

### Абсолютные пути

Можно использовать абсолютные пути:

```json
{
  "template_path": "C:/Templates/template.pptx",
  "slides": [
    {
      "notes_source": "C:/Notes/slide1.md",
      "images": ["C:/Images/photo.jpg"]
    }
  ]
}
```

### Смешивание путей

Можно комбинировать абсолютные и относительные пути в одном файле:

```json
{
  "template_path": "C:/Templates/corporate.pptx",
  "slides": [
    {
      "notes_source": "notes/slide1.md",
      "images": ["../shared/logo.png"]
    }
  ]
}
```

---

## Markdown заметки

### Поддержка Markdown

Система автоматически конвертирует Markdown в plain text для заметок PowerPoint.

**Поддерживаемые элементы:**

- Заголовки (`#`, `##`, etc.)
- Жирный текст (`**текст**`)
- Курсив (`*текст*`)
- Списки (нумерованные и маркированные)
- Ссылки
- Цитаты
- Код-блоки
- Таблицы

### Inline текст vs файлы

**Вариант 1: Markdown файл**

```json
{
  "notes_source": "notes/slide1.md"
}
```

**Вариант 2: Inline текст**

```json
{
  "notes_source": "Это обычный текст заметки"
}
```

Система автоматически определяет, является ли `notes_source` путем к файлу или inline текстом:

- Если файл существует → загружается содержимое
- Если файла нет → используется как inline текст

### Примеры Markdown файлов

См. `doc/samples/notes1.md` и `doc/samples/notes2.md`.

### Legacy поддержка

Старые конфигурации с полем `notes_text` автоматически мигрируются:

```json
// Старый формат (работает)
{
  "notes_text": "Заметка"
}

// Новый формат (рекомендуется)
{
  "notes_source": "Заметка"
}
```

---

## Расширяемость

### Добавление новых макетов

Макеты регистрируются в `config/settings.py`.

**Шаг 1:** Создайте `LayoutBlueprint`:

```python
from models.layout_registry import LayoutBlueprint, ImagePlacement
from pptx.util import Inches

my_custom_layout = LayoutBlueprint(
    name="my_custom",
    placeholders={
        "TITLE": 0,
        "NUMBER": 1,
        "IMAGE_1": 10,
        "IMAGE_2": 11
    },
    image_placements=[
        ImagePlacement(
            placeholder_idx=10,
            left=Inches(1),
            top=Inches(2),
            width=Inches(4),
            height=Inches(3)
        ),
        ImagePlacement(
            placeholder_idx=11,
            left=Inches(6),
            top=Inches(2),
            width=Inches(4),
            height=Inches(3)
        )
    ]
)
```

**Шаг 2:** Зарегистрируйте макет:

```python
from config.settings import register_default_layouts
from models.layout_registry import get_layout_registry

# После регистрации дефолтных макетов
register_default_layouts()

# Добавьте свой
registry = get_layout_registry()
registry.register(my_custom_layout)
```

**Шаг 3:** Используйте в JSON:

```json
{
  "layout_name": "my_custom",
  ...
}
```

### Анализ шаблона для новых макетов

Используйте команду `analyze` для изучения структуры вашего шаблона:

```bash
python main.py analyze --template template.pptx --layout "Your Layout Name"
```

Это покажет:

- Индексы placeholder'ов
- Типы placeholder'ов (TITLE, PICTURE, etc.)
- Координаты и размеры

Используйте эту информацию для создания `LayoutBlueprint`.

---

## Миграция со старых версий

### Миграция one.py, two.py, three.py

Старые скрипты находятся в архиве (`archive/` после очистки).

**Изменения:**

1. **Вместо прямого запуска Python скриптов** → CLI команды

   ```bash
   # Было
   python three.py config.json
   
   # Стало
   python main.py generate --config config.json
   ```

2. **Поле `notes_text`** → `notes_source`

   ```json
   // Было
   {"notes_text": "Текст"}
   
   // Стало (backward compatible)
   {"notes_source": "Текст"}
   ```

3. **Inline текст vs MD файлы**
   - Старая версия: только inline текст
   - Новая версия: поддержка MD файлов + inline текст

### Автоматическая миграция

Система автоматически мигрирует `notes_text` → `notes_source` при загрузке старых конфигов.

---

## Troubleshooting

### Ошибка: "Layout not found"

**Проблема:** Указанный макет не найден в шаблоне.

**Решение:**

1. Проверьте список доступных макетов:

   ```bash
   python main.py analyze --template template.pptx
   ```

2. Убедитесь, что имя макета указано правильно (case-sensitive)
3. Проверьте, что макет зарегистрирован в `config/settings.py`

### Ошибка: "Image not found"

**Проблема:** Изображение не найдено по указанному пути.

**Решение:**

1. Проверьте, что путь указан правильно
2. Если используете относительные пути, убедитесь, что они указаны относительно JSON файла
3. Используйте `--verbose` для подробной диагностики:

   ```bash
   python main.py generate --config config.json --verbose
   ```

### Ошибка: "Mismatch between images and placements"

**Проблема:** Количество изображений не соответствует количеству размещений в макете.

**Поведение:**

- Если изображений **больше** → лишние игнорируются (предупреждение)
- Если изображений **меньше** → некоторые placeholder'ы останутся пустыми (предупреждение)

**Решение:**

1. Проверьте количество изображений в слайде
2. Убедитесь, что используете правильный макет:
   - `single_wide` / `single_tall` → 1 изображение
   - `two_stack` / `two_tall_row` → 2 изображения

---

## Дополнительные ресурсы

- **План рефакторинга:** `doc/plan/refactor_plan.md`
- **Полный pipeline:** `doc/full_pipeline.md`
- **Тесты:** `tests/README.md`
- **Примеры конфигураций:** `doc/samples/`

---

## Поддержка

При возникновении проблем:

1. Проверьте логи с флагом `--verbose`
2. Убедитесь, что все зависимости установлены
3. Проверьте формат JSON конфигурации
4. Изучите примеры в `doc/samples/`

```

## `doc/samples/audio_example.json`

```json
{
  "template_path": "templates/youtube_base.pptx",
  "layout_name": "VideoLayout",
  "output_path": "presentation_with_audio.pptx",
  "slides": [
    {
      "slide_type": "title_youtube",
      "layout_type": "title_youtube",
      "layout_name": "TitleLayout",
      "title": "Мой YouTube Канал",
      "subtitle": "Презентация с озвучкой",
      "series_number": "Часть 1",
      "notes_source": "Титульный слайд с аудио вступлением",
      "images": ["channel_logo.png"],
      "audio": "audio/intro.mp3"
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Введение",
      "notes_source": "Первый слайд с голосовой озвучкой",
      "images": ["slide1.jpg"],
      "audio": "audio/slide1_voiceover.mp3"
    },
    {
      "slide_type": "content",
      "layout_type": "two_stack",
      "title": "Примеры кода",
      "notes_source": "Слайд без аудио - обычный контент",
      "images": ["code_example1.png", "code_example2.png"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Заключение",
      "notes_source": "Финальный слайд с музыкальным фоном",
      "images": ["conclusion.jpg"],
      "audio": "audio/outro_music.wav"
    }
  ]
}

```

## `doc/samples/mixed_layouts_example.json`

```json
{
  "template_path": "templates/youtube_base.pptx",
  "layout_name": "ContentLayout",
  "output_path": "mixed_layouts_presentation.pptx",
  "slides": [
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "layout_name": "TitleLayout",
      "title": "Заголовок презентации",
      "notes_source": "Это титульный слайд презентации. Использует специальный макет TitleLayout с крупным заголовком и обложкой на весь слайд.",
      "images": ["cover.jpg"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Введение",
      "notes_source": "Первый контентный слайд. Использует глобальный макет ContentLayout (layout_name не указан).",
      "images": ["intro.jpg"]
    },
    {
      "slide_type": "content",
      "layout_type": "two_stack",
      "title": "Сравнение",
      "notes_source": "Слайд с двумя изображениями вертикально. Также использует ContentLayout.",
      "images": ["before.jpg", "after.jpg"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "layout_name": "SectionLayout",
      "title": "Раздел 2: Практика",
      "notes_source": "Разделитель раздела. Использует специальный макет SectionLayout с ярким фоном.",
      "images": ["section2_divider.jpg"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_tall",
      "title": "Мобильный интерфейс",
      "notes_source": "Демонстрация вертикального скриншота. ContentLayout.",
      "images": ["mobile_screen.jpg"]
    },
    {
      "slide_type": "content",
      "layout_type": "two_tall_row",
      "title": "Варианты дизайна",
      "notes_source": "Сравнение двух вариантов интерфейса. ContentLayout.",
      "images": ["variant_a.jpg", "variant_b.jpg"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "layout_name": "TitleLayout",
      "title": "Заключение",
      "notes_source": "Финальный слайд. Снова используем TitleLayout для акцента.",
      "images": ["conclusion.jpg"]
    }
  ]
}

```

## `doc/samples/slides_config.json`

```json
{
  "template_path": "templates/youtube_base.pptx",
  "layout_name": "VideoLayout",
  "output_path": "c:\\PY\\presentation_mcp\\output.pptx",
  "slides": [
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Качаем VS Code",
      "notes_source": "Сейчас мы должны скачать VS Code\n- Пункт 1 - Скачать\n- Пункт 2 - Установить",
      "images": [
        "c:\\PY\\presentation_mcp\\images\\Страница_загрузки_Visual_Studio_Code_с_вариантами_для_Windows_Linux_и_Mac.png"
      ]
    },
    {
      "slide_type": "content",
      "layout_type": "single_tall",
      "title": "Обзор расширений VS Code",
      "notes_source": "Вот такие есть расширения для Python в VS Code...",
      "images": [
        "c:\\PY\\presentation_mcp\\images\\Список_расширений_VS_Code_для_Python.png"
      ]
    },
    {
      "slide_type": "content",
      "layout_type": "two_stack",
      "title": "Cline и Excalidraw",
      "notes_source": "На двух скриншотах мы видим расширения Cline и Excalidraw для VS Code.",
      "images": [
        "c:\\PY\\presentation_mcp\\images\\Карточка_расширения_Cline_в_VS_Code.png",
        "c:\\PY\\presentation_mcp\\images\\Карточка_расширения_Excalidraw_в_VS_Code.png"
      ]
    },
    {
      "slide_type": "content",
      "layout_type": "two_tall_row",
      "title": "Спасибо за внимание!",
      "notes_source": "Если есть вопросы, задавайте их сейчас.",
      "images": [
        "c:\\PY\\presentation_mcp\\images\\Список_расширений_VS_Code_для_Python.png",
        "c:\\PY\\presentation_mcp\\images\\Список_расширений_VS_Code_для_Python.png"
      ]
    }
  ]
}

```

## `doc/samples/test_three_stack.json`

```json
{
  "template_path": "templates/youtube_base.pptx",
  "layout_name": "VideoLayout",
  "output_path": "c:\\PY\\presentation_mcp\\output_three_stack.pptx",
  "slides": [
    {
      "slide_type": "content",
      "layout_type": "three_stack",
      "title": "Три шага установки",
      "notes_source": "На этом слайде показаны три последовательных шага установки VS Code:\n- Шаг 1: Скачивание\n- Шаг 2: Установка расширений\n- Шаг 3: Настройка",
      "images": [
        "c:\\PY\\presentation_mcp\\images\\Страница_загрузки_Visual_Studio_Code_с_вариантами_для_Windows_Linux_и_Mac.png",
        "c:\\PY\\presentation_mcp\\images\\Карточка_расширения_Cline_в_VS_Code.png",
        "c:\\PY\\presentation_mcp\\images\\Карточка_расширения_Excalidraw_в_VS_Code.png"
      ]
    }
  ]
}

```

## `doc/samples/youtube_title_example.json`

```json
{
  "template_path": "templates/youtube_base.pptx",
  "layout_name": "VideoLayout",
  "output_path": "youtube_presentation.pptx",
  "slides": [
    {
      "slide_type": "title_youtube",
      "layout_type": "title_youtube",
      "layout_name": "TitleLayout",
      "title": "Мой Канал о Python",
      "subtitle": "Полное руководство для начинающих",
      "series_number": "Часть 1",
      "notes_source": "Добро пожаловать на мой канал! Сегодня мы начинаем серию видео о Python.",
      "images": ["images/channel_logo_square.png"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Установка Python",
      "notes_source": "В этом разделе мы рассмотрим процесс установки Python на разные операционные системы.",
      "images": ["images/python_download_page.png"]
    },
    {
      "slide_type": "content",
      "layout_type": "two_stack",
      "title": "Первая программа",
      "notes_source": "Напишем классическое 'Hello World' и запустим его в терминале.",
      "images": ["images/hello_code.png", "images/hello_output.png"]
    }
  ]
}

```

## `doc/TEMPLATE_GUIDE.md`

```md
# 🎨 Руководство по созданию PowerPoint шаблонов

## 🎯 Цель документа

Научить создавать **один файл `.pptx` с несколькими макетами слайдов**, который система сможет использовать для генерации разных типов слайдов в одной презентации.

---

## ⚠️ КРИТИЧЕСКИ ВАЖНО: Архитектура шаблонов

### ✅ Правильный подход

**ОДИН файл шаблона с НЕСКОЛЬКИМИ макетами внутри**

```
youtube_base.pptx
├── TitleLayout     (для титульных слайдов)
├── VideoLayout     (для контентных слайдов)
└── SectionLayout   (опционально, для разделителей)
```

### ❌ НЕПРАВИЛЬНЫЙ подход

**Несколько файлов шаблонов** — технически невозможно с `python-pptx`!

```
❌ youtube_title.pptx  (для титульных)
❌ youtube_content.pptx (для контента)
```

**Почему нельзя?**

- `python-pptx` создает **один** объект `Presentation` из **одного** `.pptx` файла
- Библиотека не умеет объединять слайды из разных презентаций
- Попытка загрузить второй файл перезапишет первый

---

## 🏗️ Ключевые принципы

### 1. Работаем только в "Образце слайдов" (Slide Master)

**НЕ рисуйте на обычном слайде!** Обычные текстовые блоки для Python — "мусор" без стабильных ID.

Python работает только с **Заполнителями** (Placeholders) из Образца:

- Стабильные индексы (`idx=10`, `idx=11`, `idx=12`)
- Предсказуемое поведение
- Наследование от Master Slide

### 2. Один Master → Несколько Layouts

- **Master Slide** (родитель) — содержит общие настройки (фон, шрифты)
- **Layouts** (макеты) — наследуют от Master, добавляют свои placeholders

---

## 📋 Пошаговая инструкция: Создание шаблона с двумя макетами

### Шаг 1: Создайте базовый файл

1. **Откройте PowerPoint**
   - Создайте пустую презентацию (`Ctrl+N`)
   - Удалите титульный слайд (если есть)

2. **Войдите в режим Образца слайдов**
   - Вкладка **"Вид"** (View)
   - Нажмите **"Образец слайдов"** (Slide Master)

**Что вы видите:**

- Слева — иерархия слайдов
- Сверху большой слайд — **Master Slide** (родитель)
- Ниже с отступом — **Layouts** (макеты-дети)

---

### Шаг 2: Настройте Master Slide (общий фон)

1. **Выберите Master** (самый верхний слайд)

2. **Установите фон**
   - Вкладка **"Образец слайдов"** → **"Стили фона"** → **"Формат фона..."**
   - Выберите **"Сплошная заливка"**
   - Цвет: черный (`#000000`) или темно-серый (`#1A1A1A`)

3. **Настройте шрифты (опционально)**
   - Master Slide → **"Шрифты"** → выберите нужное семейство

✅ **Результат:** Все макеты унаследуют этот фон автоматически

---

### Шаг 3: Создайте TitleLayout (для титульных слайдов)

#### 3.1 Очистите и переименуйте первый макет

1. Удалите все макеты кроме одного
2. Правой кнопкой на оставшийся → **"Переименовать макет"**
3. Введите: `TitleLayout`

#### 3.2 Добавьте placeholders для TitleLayout

**Нужны 3 заполнителя:**

**Placeholder 1: Title (заголовок)**

- **Вставка** → **"Заполнитель"** → **"Текст"**
- Разместите: крупно, по центру
- Шрифт: **48-72pt**, жирный, белый

**Placeholder 2: Slide Number (номер слайда)**

- **Вставка** → **"Заполнитель"** → **"Текст"**
- Разместите: правый нижний угол, мелко
- Шрифт: **12-14pt**, белый

**Placeholder 3: Subtitle (подзаголовок)**

- **Вставка** → **"Заполнитель"** → **"Текст"**
- Разместите: под заголовком
- Шрифт: **24-32pt**, белый

**⚠️ ВАЖНО:** Placeholders создаются через **Вставка → Заполнитель**, а НЕ через обычную "Надпись"!

#### 3.3 Проверьте индексы

После создания запустите анализ:

```bash
python main.py analyze youtube_base.pptx -l TitleLayout
```

**Должно быть:**

```
idx=10 (Title)       ← заголовок
idx=12 (???)         ← номер слайда
idx=13 (Subtitle)    ← подзаголовок
```

**Почему idx=12 для номера, а не idx=11?** Это нормально — PowerPoint сам назначает индексы при создании.

---

### Шаг 4: Создайте VideoLayout (для контентных слайдов)

#### 4.1 Дублируйте TitleLayout

- Правой кнопкой на `TitleLayout` → **"Дублировать макет"**

#### 4.2 Переименуйте

- Правой кнопкой → **"Переименовать"** → `VideoLayout`

#### 4.3 Измените дизайн

**Удалите Subtitle:**

- Кликните на placeholder Subtitle
- Нажмите `Delete`
- Остается только Title и Slide Number

**Опционально:** Добавьте декоративные элементы (логотип, линии)

#### 4.4 Проверьте индексы

```bash
python main.py analyze youtube_base.pptx -l VideoLayout
```

**Должно быть:**

```
idx=10 (Title)        ← заголовок
idx=11 (Slide Number) ← номер
```

---

### Шаг 5: Сохраните шаблон

1. **Выйдите из режима Образца**
   - Вид → **"Закрыть режим образца"**

2. **Сохраните файл**
   - Файл → **"Сохранить как..."**
   - Имя: `youtube_base.pptx`
   - Расположение: `templates/`

---

## 🧪 Проверка готового шаблона

### 1. Список макетов

```bash
python main.py analyze templates/youtube_base.pptx --list
```

**Ожидаемый результат:**

```
📋 Макеты в youtube_base.pptx:
  1. TitleLayout
  2. VideoLayout
```

### 2. Placeholders в TitleLayout

```bash
python main.py analyze templates/youtube_base.pptx -l TitleLayout
```

**Требуется:**

- idx=10 (Title) ✅
- idx=12 или idx=11 (Slide Number) ✅
- idx=13 или idx=12 (Subtitle) ✅

### 3. Placeholders в VideoLayout

```bash
python main.py analyze templates/youtube_base.pptx -l VideoLayout
```

**Требуется:**

- idx=10 (Title) ✅
- idx=11 (Slide Number) ✅

---

## 📝 Использование в JSON

### Пример: Титульный + Контентные слайды

```json
{
  "template_path": "templates/youtube_base.pptx",
  "layout_name": "VideoLayout",
  "output_path": "output.pptx",
  "slides": [
    {
      "slide_type": "title_youtube",
      "layout_type": "title_youtube",
      "layout_name": "TitleLayout",
      "title": "Название канала",
      "subtitle": "Описание серии",
      "images": ["logo.png"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Контентный слайд 1",
      "images": ["image1.png"]
    },
    {
      "slide_type": "content",
      "layout_type": "two_stack",
      "title": "Контентный слайд 2",
      "images": ["img1.png", "img2.png"]
    }
  ]
}
```

**Ключевые моменты:**

- `template_path`: **один** файл для всех слайдов
- `layout_name` (глобальный): `VideoLayout` по умолчанию
- `layout_name` (в слайде): `TitleLayout` для титульного (переопределяет глобальный)

---

## 🎨 Настройка индексов в коде

После создания шаблона **обязательно обновите** `config/settings.py`:

```python
# VideoLayout (контентные слайды):
PLACEHOLDER_TITLE_IDX = 10
PLACEHOLDER_SLIDE_NUM_IDX = 11

# TitleLayout (титульные слайды YouTube):
PLACEHOLDER_TITLE_LAYOUT_TITLE_IDX = 10
PLACEHOLDER_TITLE_LAYOUT_SLIDE_NUM_IDX = 12  # или 11, смотрите analyze
PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX = 13   # или 12, смотрите analyze
```

**Как узнать правильные значения?** Используйте `analyze`:

```bash
python main.py analyze templates/youtube_base.pptx -l TitleLayout
```

---

## ❓ FAQ

### Q: Можно ли использовать несколько `.pptx` файлов?

**A:** ❌ **НЕТ!** `python-pptx` технически не позволяет объединять слайды из разных презентаций. Используйте **один файл с несколькими макетами**.

### Q: Сколько макетов можно создать?

**A:** ✅ Сколько угодно! Создайте:

- `TitleLayout` (титульные)
- `VideoLayout` (контент)
- `SectionLayout` (разделители)
- `OutroLayout` (заключение)

Все в **одном файле**.

### Q: Что делать, если idx отличаются от примера?

**A:** ✅ Это нормально! PowerPoint сам назначает индексы. Главное:

1. Запустите `analyze`
2. Обновите константы в `config/settings.py`
3. Проверьте работу тестовой презентацией

### Q: Нужно ли менять код при создании нового шаблона?

**A:** Только если меняются **индексы placeholders**. Если создаёте новые макеты с теми же idx — код трогать не нужно.

---

## 🚀 Быстрый старт: Готовый пример

**У вас уже есть рабочий шаблон:** `templates/youtube_base.pptx`

```bash
# 1. Проверьте шаблон
python main.py analyze templates/youtube_base.pptx --list

# 2. Создайте тестовую презентацию
python main.py generate test_youtube_base.json

# 3. Откройте результат
TEST_youtube_base.pptx
```

✅ Работает? Используйте его как основу для своих шаблонов!

---

## 📚 Дополнительная информация

- **Полный справочник:** [REFERENCE.md](REFERENCE.md)
- **Примеры JSON:** [samples/](samples/)
- **MCP инструкция:** [MCP_USAGE.md](MCP_USAGE.md)

---

**Дата обновления:** 19 ноября 2025  
**Версия:** 2.0 (Multiple Layouts)

**⚠️ ВАЖНО:** Теперь кликните обратно на **свой макет** `VideoLayout` (маленький слайд).

#### 4.1. Создайте Заголовок

1. **Вставьте заполнитель**
   - Убедитесь, что вы на вкладке **"Образец слайдов"**
   - Нажмите **"Вставить заполнитель"** (Insert Placeholder) → **"Текст"** (Text)

2. **Нарисуйте прямоугольник**
   - Нарисуйте область там, где должен быть заголовок
   - Обычно: верхняя часть слайда, по центру или слева

3. **Очистите от мусора**
   - Кликните на созданный заполнитель
   - Вы увидите текст "Образец текста" с несколькими уровнями
   - **Удалите все уровни, кроме первого**
   - Выделите оставшуюся строку
   - На вкладке **"Главная"** (Home) **ОТОЖМИТЕ кнопку "Маркеры"** (Bullets)

4. **Настройте стиль**
   - Шрифт: например, Arial или Calibri
   - Размер: 32-44 pt (для заголовка)
   - Цвет: **светлый** (белый `#FFFFFF`, светло-серый `#E0E0E0`)
   - Выравнивание: по вашему выбору

#### 4.2. Создайте Номер слайда

1. **Вставьте второй заполнитель**
   - Снова **"Вставить заполнитель"** → **"Текст"**

2. **Нарисуйте маленький блок**
   - Обычно: правый нижний угол или на желтом круге
   - Размер: небольшой квадрат или прямоугольник

3. **Повторите очистку**
   - Удалите лишние уровни
   - Отожмите маркеры

4. **Настройте стиль**
   - Шрифт: жирный (Bold)
   - Размер: 12-16 pt
   - Цвет: зависит от фона (темный для желтого круга, светлый для темного фона)
   - Выравнивание: по центру

**✅ Результат:** Вы создали два "адреса", по которым Python будет вставлять текст.

---

### Шаг 5: Нарисуйте "Декорации" (Статичные фигуры)

**Цель:** Добавить визуальные элементы, которые будут на каждом слайде.

**⚠️ Убедитесь:** Вы все еще на макете `VideoLayout`, а не на Master.

#### Пример: Желтый круг для номера слайда

1. **Вставьте фигуру**
   - Вкладка **"Вставка"** (Insert) → **"Фигуры"** (Shapes) → **"Овал"** (Oval)

2. **Нарисуйте круг**
   - Удерживайте `Shift` при рисовании для ровного круга
   - Установите цвет заливки: желтый `#FFD700`
   - Уберите контур (No Outline)

3. **Отправьте на задний план**
   - Кликните на круг **правой кнопкой мыши**
   - Выберите **"На задний план"** (Send to Back)

4. **Позиционируйте**
   - Подвигайте круг так, чтобы ваш "Заполнитель номера" оказался на его фоне

**Другие примеры декораций:**

- Логотип компании в углу
- Разделительные линии
- Декоративные элементы
- Водяной знак

---

### Шаг 6: Определите зону для изображений (⚠️ ВАЖНО: Пустота!)

#### ❓ Вопрос: Куда вставлять скриншоты/изображения?

#### ✅ Ответ: НИКУДА. Просто оставьте пустое место

#### ПОЧЕМУ?

**Если вы добавите "Заполнитель изображения" (Picture Placeholder):**

- PowerPoint будет **растягивать** и **обрезать** (crop) ваши изображения
- Это **исказит пропорции** (16:9 станет 4:3 и т.д.)
- Вы потеряете контроль над масштабированием

**Правильный подход:**

- Python-скрипт использует **абсолютные координаты** (в дюймах)
- Изображения вставляются поверх пустого места
- Масштабирование происходит с **сохранением пропорций**
- Гарантируется точное размещение

#### Как это работает в коде

```python
# В config/settings.py вы задаете координаты:
ImagePlacement(
    placeholder_idx=10,  # Не используется для изображений
    left=Inches(0.5),    # Отступ слева
    top=Inches(2.0),     # Отступ сверху
    width=Inches(9.0),   # Ширина зоны
    height=Inches(5.0)   # Высота зоны
)
```

#### Что делать

1. **Визуально оцените** пространство на макете
2. **Запомните**, где должны быть изображения
3. **НЕ добавляйте** Picture Placeholder
4. **Оставьте** эту область пустой

**После создания шаблона** вы используете команду `analyze`, чтобы получить точные координаты.

---

### Шаг 7: Сохраните "Чертеж"

1. **Выйдите из режима Образца**
   - На вкладке **"Образец слайдов"**
   - Нажмите **"Закрыть режим образца"** (Close Master View)

2. **Проверьте результат**
   - Экран должен стать пустым (или показать ваш макет)
   - Это нормально — у вас нет обычных слайдов

3. **Сохраните файл**
   - **"Файл"** → **"Сохранить как"**
   - Имя: `template.pptx`
   - Место: папка вашего проекта

**✅ Готово!** Ваш шаблон создан.

---

## 🔍 Шаг 8: Запустите "Сканер" (Анализ шаблона)

### Цель: Узнать индексы (idx) ваших заполнителей

1. **Запустите команду анализа**

   ```bash
   python main.py analyze templates/youtube_base.pptx
   ```

2. **Вы получите вывод:**

   ```
   📊 Анализ шаблона: youtube_base.pptx
   🎨 Макет: VideoLayout
   
   Заполнители:
   📌 Заполнитель IDX = 10
      Тип: BODY (2)
      Имя: Текст 5
      Текст: Образец текста
   
   📌 Заполнитель IDX = 11
      Тип: BODY (2)
      Имя: Текст 8
      Текст: 2
   ```

3. **Что означают индексы:**
   - `idx 10` — ваш **Заголовок**
   - `idx 11` — ваш **Номер слайда**

4. **Для титульного шаблона youtube_title.pptx:**

   ```bash
   python main.py analyze templates/youtube_title.pptx
   ```

   Вывод покажет 3 заполнителя:
   - `idx 10` — **Заголовок** (название канала)
   - `idx 11` — **Номер слайда**
   - `idx 12` — **Subtitle** (подзаголовок/описание серии)

---

## 📝 Регистрация макета в коде

### Откройте файл `config/settings.py`

```python
from models.layout_registry import LayoutBlueprint, ImagePlacement
from pptx.util import Inches

def register_default_layouts():
    """Регистрирует стандартные макеты"""
    registry = get_layout_registry()
    
    # Ваш новый макет
    video_layout = LayoutBlueprint(
        name="VideoLayout",  # ← То самое имя из Шага 2!
        placeholders={
            "TITLE": 0,      # ← idx из analyze
            "NUMBER": 1      # ← idx из analyze
        },
        image_placements=[
            ImagePlacement(
                placeholder_idx=10,  # Любое число (не используется)
                left=Inches(0.5),    # Координаты из analyze
                top=Inches(2.0),
                width=Inches(9.0),
                height=Inches(5.0)
            )
        ]
    )
    
    registry.register(video_layout)
```

---

## 🎨 Примеры готовых макетов

### 1. Одно широкое изображение (16:9)

```
┌─────────────────────────────────────┐
│          ЗАГОЛОВОК                  │
├─────────────────────────────────────┤
│                                     │
│       [Широкое изображение]         │
│                                     │
└─────────────────────────────────────┘
```

**Использование:** пейзажи, скриншоты, диаграммы

### 2. Одно высокое изображение (9:16)

```
┌──────────────┬──────────────────┐
│  ЗАГОЛОВОК   │                  │
├──────────────┤  [Высокое        │
│              │   изображение]   │
│              │                  │
└──────────────┴──────────────────┘
```

**Использование:** портреты, мобильные скриншоты

### 3. Два изображения вертикально

```
┌─────────────────────────────────────┐
│          ЗАГОЛОВОК                  │
├─────────────────────────────────────┤
│      [Изображение 1]                │
├─────────────────────────────────────┤
│      [Изображение 2]                │
└─────────────────────────────────────┘
```

**Использование:** сравнение "до/после", этапы

### 4. Два высоких изображения рядом

```
┌──────────────┬──────────────────┐
│  ЗАГОЛОВОК   │                  │
├──────────────┼──────────────────┤
│ [Изображение │  [Изображение 2] │
│      1]      │                  │
└──────────────┴──────────────────┘
```

**Использование:** сравнение версий, варианты дизайна

---

## 🔧 Продвинутые техники

### Использование нескольких макетов в одном шаблоне

**Новая возможность:** Теперь вы можете использовать разные макеты PowerPoint в одной презентации!

#### Сценарий: Титульный слайд + контентные слайды

1. **Создайте несколько макетов** в одном `template.pptx`
   - `TitleLayout` — для титульного слайда (обложки)
   - `ContentLayout` — для обычных контентных слайдов
   - `SectionLayout` — для разделителей разделов (опционально)

2. **В JSON конфигурации** указывайте нужный макет для каждого слайда:

   ```json
   {
     "template_path": "template.pptx",
     "layout_name": "ContentLayout",
     "slides": [
       {
         "layout_type": "single_wide",
         "layout_name": "TitleLayout",
         "title": "Заголовок презентации",
         "notes_source": "Обложка курса",
         "images": ["cover.jpg"]
       },
       {
         "layout_type": "single_wide",
         "title": "Введение",
         "notes_source": "Первый контентный слайд",
         "images": ["intro.jpg"]
       },
       {
         "layout_type": "two_stack",
         "layout_name": "SectionLayout",
         "title": "Раздел 2",
         "notes_source": "Разделитель",
         "images": ["section2.jpg"]
       }
     ]
   }
   ```

**Как это работает:**

1. **Глобальный `layout_name`** — `ContentLayout` используется по умолчанию
2. **Первый слайд** переопределяет через `"layout_name": "TitleLayout"`
3. **Второй слайд** использует глобальный `ContentLayout` (не указан layout_name)
4. **Третий слайд** переопределяет через `"layout_name": "SectionLayout"`

#### Создание титульного макета

**Отличия титульного слайда от контентного:**

| Элемент | Титульный слайд | Контентный слайд |
|---------|----------------|------------------|
| Заголовок | Крупный, по центру | Обычный размер, сверху |
| Изображение | На весь слайд | Часть слайда |
| Декорации | Логотип, дата, автор | Номер слайда |
| Фон | Может быть ярким | Нейтральный |

**Пример создания титульного макета:**

1. В режиме Образца создайте макет `TitleLayout`
2. Заполнитель заголовка — крупный шрифт, по центру
3. Добавьте декоративные элементы (логотип, линии)
4. Оставьте пространство для большого изображения-обложки
5. Зарегистрируйте в `config/settings.py` с теми же индексами заполнителей

### Наследование стилей от Master

**Совет:** Настройте шрифты и цвета на Master Slide (большом), и все макеты унаследуют эти стили.

**Что настраивать на Master:**

- Семейство шрифтов
- Цветовая схема
- Фон по умолчанию
- Стили заголовков

**Что настраивать на Layout:**

- Расположение заполнителей
- Уникальные декорации
- Специфичные стили

---

## ❓ Частые вопросы

### В: Можно ли использовать существующий шаблон компании?

**О:** Да! Откройте его в режиме Образца, создайте новый макет или модифицируйте существующий.

### В: Что делать, если у меня сложный дизайн с множеством элементов?

**О:**

1. Разделите на статичные элементы (декорации) и динамичные (заполнители)
2. Статичные рисуйте как фигуры на макете
3. Динамичные создавайте как заполнители
4. Используйте команду `analyze` для проверки

### В: Можно ли изменить шаблон после создания презентаций?

**О:** Да, но:

- Уже созданные презентации не обновятся автоматически
- Новые презентации будут использовать новый дизайн
- Индексы (idx) должны оставаться теми же

### В: Нужно ли создавать заполнитель для изображений?

**О:** **НЕТ!** Оставьте пустое место. Python вставляет изображения по абсолютным координатам с сохранением пропорций.

### В: Как узнать точные координаты для изображений?

**О:** Используйте `python main.py analyze --template template.pptx --layout "LayoutName"` и измерьте свободное пространство.

---

## 🚀 Следующие шаги

1. **Создайте свой первый шаблон** по этому руководству
2. **Проанализируйте его** командой `analyze`
3. **Зарегистрируйте макет** в `config/settings.py`
4. **Создайте JSON конфигурацию** с использованием вашего макета
5. **Сгенерируйте презентацию** командой `generate`

---

## 📚 Дополнительные ресурсы

- **[REFERENCE.md](REFERENCE.md)** — полная справка по всем возможностям
- **[README.md](../README.md)** — обзор проекта и быстрый старт
- **[samples/](samples/)** — примеры готовых конфигураций
- **[config/settings.py](../config/settings.py)** — примеры регистрации макетов

---

**🎉 Поздравляем! Теперь вы можете создавать "пуленепробиваемые" шаблоны для автоматизации презентаций!**

```

## `io_handlers/__init__.py`

```py
"""
Обработчики ввода-вывода Auto-Slide.

Этот пакет содержит компоненты для:
- Загрузки и валидации JSON конфигураций
- Разрешения путей (абсолютных и относительных)
- Загрузки ресурсов (Markdown файлов, изображений)
"""

from .path_resolver import PathResolver
from .config_loader import ConfigLoader
from .resource_loader import ResourceLoader

__all__ = [
    "PathResolver",
    "ConfigLoader",
    "ResourceLoader",
]

```

## `io_handlers/config_loader.py`

```py
"""
Загрузка и валидация JSON конфигураций.

Этот модуль отвечает за чтение JSON файлов и преобразование их
в типизированные dataclass объекты.
"""

import json
import logging
from pathlib import Path
from typing import Union, Dict, Any

from models import PresentationConfig, SlideConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Загрузчик конфигураций презентаций из JSON.

    Example:
        >>> loader = ConfigLoader()
        >>> config = loader.load(Path("config.json"))
        >>> print(f"Слайдов: {len(config.slides)}")
    """

    @staticmethod
    def load(json_path: Union[str, Path]) -> PresentationConfig:
        """
        Загружает и валидирует JSON конфигурацию.

        Args:
            json_path: Путь к JSON файлу конфигурации.

        Returns:
            Валидированный объект PresentationConfig.

        Raises:
            FileNotFoundError: Если файл не найден.
            json.JSONDecodeError: Если JSON невалиден.
            ValueError: Если структура JSON не соответствует схеме.

        Example:
            >>> config = ConfigLoader.load("presentation.json")
        """
        json_path = Path(json_path)

        logger.info(f"📥 Загрузка конфигурации: {json_path}")

        if not json_path.exists():
            error_msg = f"Конфигурационный файл не найден: {json_path}"
            logger.error(f"❌ {error_msg}")
            raise FileNotFoundError(error_msg)

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
                # Логируем первые 500 символов raw JSON для отладки
                logger.debug(
                    f"🔍 Сырые данные JSON (первые 500 символов): {raw_content[:500]}"
                )
                data = json.loads(raw_content)
        except json.JSONDecodeError as e:
            logger.error(
                "❌ Не удалось загрузить конфигурацию: ошибка парсинга JSON",
                exc_info=True,
            )
            raise json.JSONDecodeError(
                f"Ошибка парсинга JSON в {json_path}: {e.msg}", e.doc, e.pos
            )
        except Exception as e:
            logger.error(f"❌ Не удалось загрузить конфигурацию: {e}", exc_info=True)
            raise

        config = ConfigLoader._parse_config(data, json_path)
        logger.info("✅ Конфигурация загружена успешно")
        return config

    @staticmethod
    def _parse_config(data: Dict[str, Any], source_path: Path) -> PresentationConfig:
        """
        Парсит словарь в PresentationConfig.

        Args:
            data: Словарь с данными JSON.
            source_path: Путь к исходному файлу (для error messages).

        Returns:
            Объект PresentationConfig.

        Raises:
            ValueError: Если структура данных невалидна.
        """
        try:
            # Логируем применение дефолтных значений
            template_default = data.get("template_path", "template.pptx")
            layout_default = data.get("layout_name", "VideoLayout")
            logger.debug(
                f"🔧 Применение дефолтных значений: template_path={template_default}, layout_name={layout_default}"
            )

            # Извлекаем слайды
            slides_data = data.get("slides", [])
            if not isinstance(slides_data, list):
                error_msg = "Поле 'slides' должно быть массивом"
                logger.error(f"⚠️ Ошибка валидации: {error_msg}")
                raise ValueError(error_msg)

            # Парсим слайды - передаем словари напрямую!
            # PresentationConfig.__post_init__ сам вызовет фабрику
            slides_data_list = []
            for i, slide_data in enumerate(slides_data, 1):
                if not isinstance(slide_data, dict):
                    error_msg = f"Слайд #{i} должен быть объектом JSON"
                    logger.error(f"⚠️ Ошибка валидации: {error_msg}")
                    raise ValueError(error_msg)

                # Логируем сырые данные каждого слайда
                logger.debug(f"🔍 Сырые данные слайда #{i}: {slide_data}")
                slides_data_list.append(slide_data)

            # Создаём конфигурацию
            config = PresentationConfig(
                template_path=data.get("template_path", "template.pptx"),
                output_path=data.get("output_path", "output.pptx"),
                layout_name=data.get("layout_name", "VideoLayout"),
                slides=slides_data_list,  # Передаем словари!
            )

            return config

        except ValueError:
            raise
        except Exception as e:
            error_msg = f"Ошибка при парсинге конфигурации из {source_path}: {e}"
            logger.error(f"⚠️ Ошибка валидации: {error_msg}", exc_info=True)
            raise ValueError(error_msg) from e

    @staticmethod
    def _parse_slide(data: Dict[str, Any]) -> SlideConfig:
        """
        Парсит словарь в SlideConfig.

        Args:
            data: Словарь с данными слайда.

        Returns:
            Объект SlideConfig.

        Raises:
            ValueError: Если обязательные поля отсутствуют.
        """
        # Поддержка legacy поля 'notes_text' (миграция)
        notes_source = data.get("notes_source")
        if notes_source is None:
            notes_source = data.get("notes_text", "")

        slide = SlideConfig(
            layout_type=data.get("layout_type", ""),
            title=data.get("title", ""),
            notes_source=notes_source,
            images=data.get("images", []),
        )

        return slide

    @staticmethod
    def save(config: PresentationConfig, json_path: Union[str, Path]) -> None:
        """
        Сохраняет конфигурацию в JSON файл.

        Args:
            config: Конфигурация для сохранения.
            json_path: Путь для сохранения JSON.

        Example:
            >>> ConfigLoader.save(config, "output_config.json")
        """
        json_path = Path(json_path)

        logger.info(f"💾 Сохранение конфигурации в: {json_path}")
        logger.debug(f"📊 Количество слайдов для сохранения: {len(config.slides)}")

        # Используем to_dict() из BaseSlideConfig для сериализации
        data = {
            "template_path": config.template_path,
            "output_path": config.output_path,
            "layout_name": config.layout_name,
            "slides": [slide.to_dict() for slide in config.slides],
        }

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("✅ Конфигурация сохранена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения конфигурации: {e}", exc_info=True)
            raise

```

## `io_handlers/path_resolver.py`

```py
"""
Разрешение путей к файлам.

Этот модуль обеспечивает корректную работу с относительными и абсолютными путями.
Относительные пути разрешаются относительно директории JSON конфигурации.
"""

import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


class PathResolver:
    """
    Разрешитель путей относительно конфигурационного файла.

    Attributes:
        config_dir: Директория, в которой находится JSON конфигурация.

    Example:
        >>> resolver = PathResolver(Path("/home/user/project/config.json"))
        >>> # Относительный путь
        >>> abs_path = resolver.resolve("images/logo.png")
        >>> # Результат: /home/user/project/images/logo.png
        >>>
        >>> # Абсолютный путь
        >>> abs_path = resolver.resolve("/usr/share/images/logo.png")
        >>> # Результат: /usr/share/images/logo.png (без изменений)
    """

    def __init__(self, config_path: Union[str, Path]):
        """
        Инициализация resolver'а.

        Args:
            config_path: Путь к JSON конфигурации. Может быть строкой или Path.

        Raises:
            ValueError: Если config_path не существует или не является файлом.
        """
        self.config_path = Path(config_path).resolve()

        if not self.config_path.exists():
            raise ValueError(f"Конфигурационный файл не найден: {self.config_path}")

        if not self.config_path.is_file():
            raise ValueError(
                f"Путь должен указывать на файл, а не директорию: {self.config_path}"
            )

        self.config_dir = self.config_path.parent

    def resolve(self, path: Union[str, Path]) -> Path:
        """
        Разрешает путь (относительный или абсолютный).

        Логика:
        - Если путь абсолютный → возвращает как есть (resolve).
        - Если путь относительный → разрешает относительно config_dir.

        Args:
            path: Путь для разрешения (строка или Path).

        Returns:
            Абсолютный путь (Path объект).

        Note:
            Метод НЕ проверяет существование файла — это ответственность вызывающей стороны.

        Example:
            >>> # Относительный путь
            >>> resolver.resolve("templates/main.pptx")
            PosixPath('/home/user/project/templates/main.pptx')
            >>>
            >>> # Абсолютный путь
            >>> resolver.resolve("/usr/share/template.pptx")
            PosixPath('/usr/share/template.pptx')
        """
        path_obj = Path(path)

        if path_obj.is_absolute():
            result = path_obj.resolve()
        else:
            result = (self.config_dir / path_obj).resolve()

        logger.debug(
            f'🗂️ Резолюция пути: Input="{path}" | Base="{self.config_dir}" | Result="{result}"'
        )
        return result

    def resolve_and_check(self, path: Union[str, Path]) -> Path:
        """
        Разрешает путь И проверяет существование файла.

        Args:
            path: Путь для разрешения.

        Returns:
            Абсолютный путь к существующему файлу.

        Raises:
            FileNotFoundError: Если файл не существует.

        Example:
            >>> try:
            ...     path = resolver.resolve_and_check("missing.txt")
            ... except FileNotFoundError as e:
            ...     print(f"Ошибка: {e}")
        """
        resolved = self.resolve(path)

        if not resolved.exists():
            logger.warning(f"⚠️ Файл не найден: {resolved} (исходный путь: {path})")
            raise FileNotFoundError(
                f"Файл не найден: {resolved}\n"
                f"Исходный путь: {path}\n"
                f"Разрешён относительно: {self.config_dir}"
            )

        return resolved

    def make_relative(self, path: Union[str, Path]) -> Path:
        """
        Делает путь относительным к config_dir (обратная операция).

        Args:
            path: Абсолютный путь.

        Returns:
            Относительный путь от config_dir.

        Raises:
            ValueError: Если путь находится вне config_dir.

        Example:
            >>> abs_path = Path("/home/user/project/images/pic.png")
            >>> rel_path = resolver.make_relative(abs_path)
            >>> print(rel_path)
            images/pic.png
        """
        path_obj = Path(path).resolve()

        try:
            relative_path = path_obj.relative_to(self.config_dir)
            logger.debug(
                f'🔄 Обратная резолюция: Absolute="{path_obj}" -> Relative="{relative_path}"'
            )
            return relative_path
        except ValueError:
            error_msg = f"Путь {path_obj} находится вне директории конфигурации {self.config_dir}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

```

## `io_handlers/resource_loader.py`

```py
"""
Загрузка ресурсов (Markdown файлов, изображений).

Этот модуль обеспечивает единообразную загрузку всех внешних ресурсов,
необходимых для генерации презентации.
"""

import logging
from pathlib import Path

from .path_resolver import PathResolver

logger = logging.getLogger(__name__)


class ResourceLoader:
    """
    Загрузчик ресурсов для презентации.

    Работает совместно с PathResolver для корректного разрешения путей.

    Attributes:
        resolver: PathResolver для разрешения путей.

    Example:
        >>> resolver = PathResolver(Path("config.json"))
        >>> loader = ResourceLoader(resolver)
        >>>
        >>> # Загрузка текста заметок
        >>> notes = loader.load_notes("notes/intro.md")
        >>>
        >>> # Разрешение пути к изображению
        >>> img_path = loader.resolve_image("images/logo.png")
    """

    def __init__(self, resolver: PathResolver):
        """
        Инициализация загрузчика ресурсов.

        Args:
            resolver: PathResolver для разрешения путей.
        """
        self.resolver = resolver

    def load_notes(self, source: str) -> str:
        """
        Загружает текст заметок докладчика.

        Логика:
        - Если source заканчивается на '.md' → читает файл и возвращает содержимое.
        - Иначе → возвращает source как inline текст.

        Args:
            source: Путь к .md файлу ИЛИ inline текст.

        Returns:
            Текст заметок (в формате Markdown, очистка выполняется позже).

        Raises:
            FileNotFoundError: Если .md файл не найден.
            IOError: Если файл не удаётся прочитать.

        Example:
            >>> # Из файла
            >>> notes = loader.load_notes("notes/slide1.md")
            >>>
            >>> # Inline текст
            >>> notes = loader.load_notes("Это inline заметки")
        """
        if source.endswith(".md"):
            # Это путь к файлу
            logger.debug("🎯 Определение типа источника заметок: ФАЙЛ (.md)")
            logger.debug(f"📝 Загрузка заметок из {source}")

            try:
                md_path = self.resolver.resolve_and_check(source)
            except FileNotFoundError:
                logger.warning(f"⚠️ Не найден файл заметок: {source}")
                raise

            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return content
            except IOError as e:
                logger.error(f"❌ Ошибка чтения файла заметок: {e}", exc_info=True)
                raise IOError(f"Ошибка чтения Markdown файла {md_path}: {e}") from e
        else:
            # Это inline текст
            logger.debug("🎯 Определение типа источника заметок: INLINE текст")
            return source

    def resolve_image(self, image_path: str) -> Path:
        """
        Разрешает путь к изображению и проверяет его существование.

        Args:
            image_path: Путь к изображению (относительный или абсолютный).

        Returns:
            Абсолютный путь к изображению.

        Raises:
            FileNotFoundError: Если изображение не найдено.

        Example:
            >>> img = loader.resolve_image("images/diagram.png")
            >>> print(img)
            /home/user/project/images/diagram.png
        """
        resolved_path = self.resolver.resolve_and_check(image_path)
        file_size = resolved_path.stat().st_size
        logger.debug(f"🔍 Файл найден: {resolved_path}, Размер: {file_size} байт")
        return resolved_path

    def resolve_audio(self, audio_path: str) -> Path:
        """
        Разрешает путь к аудиофайлу и проверяет его существование.

        Args:
            audio_path: Путь к аудиофайлу (относительный или абсолютный).

        Returns:
            Абсолютный путь к аудиофайлу.

        Raises:
            FileNotFoundError: Если аудиофайл не найден.

        Example:
            >>> audio = loader.resolve_audio("audio/voiceover.mp3")
            >>> print(audio)
            /home/user/project/audio/voiceover.mp3
        """
        resolved_path = self.resolver.resolve_and_check(audio_path)
        file_size = resolved_path.stat().st_size
        logger.debug(f"🔍 Файл найден: {resolved_path}, Размер: {file_size} байт")
        return resolved_path

    def check_resource_existence(
        self, path: str, resource_type: str = "ресурс"
    ) -> bool:
        """
        Проверяет существование ресурса без выброса исключения.

        Args:
            path: Путь к ресурсу.
            resource_type: Тип ресурса для сообщения (например, "изображение", "файл").

        Returns:
            True, если ресурс существует, иначе False.

        Example:
            >>> if not loader.check_resource_existence("optional.png", "изображение"):
            ...     print("Изображение не найдено, использую заглушку")
        """
        logger.debug(f"🔍 Проверка существования {resource_type}: {path}")
        try:
            self.resolver.resolve_and_check(path)
            logger.debug(f"✅ {resource_type.capitalize()} найден: {path}")
            return True
        except FileNotFoundError:
            logger.debug(f"⚠️ {resource_type.capitalize()} не найден: {path}")
            return False

```

## `main.py`

```py
#!/usr/bin/env python3
"""
Auto-Slide: PowerPoint Automation Pipeline

Главная точка входа для CLI приложения.
Для получения помощи запустите: python main.py --help
"""

import sys
import logging
from cli import parse_args
from core import setup_logging


def main():
    """
    Главная функция CLI.

    Парсит аргументы командной строки и выполняет соответствующую команду.
    """
    # Определяем verbose режим из аргументов до парсинга
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    # Инициализируем систему логирования
    setup_logging(verbose=verbose)

    logger = logging.getLogger(__name__)
    logger.debug(f"🚀 Приложение запущено с аргументами: {sys.argv}")

    try:
        return parse_args(sys.argv[1:])
    except Exception as e:
        logger.critical(
            f"💥 Необработанное исключение на верхнем уровне: {e}", exc_info=True
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

```

## `mcp_server.py`

```py
#!/usr/bin/env python3
"""
MCP Server для Presentation Builder

Предоставляет инструмент для создания PowerPoint презентаций
через Model Context Protocol.
"""

import logging
from mcp.server.fastmcp import FastMCP
from pathlib import Path
from models import LayoutRegistry
from io_handlers import ConfigLoader, PathResolver, ResourceLoader
from core import PresentationBuilder
from config import register_default_layouts

logger = logging.getLogger(__name__)

# Создаём MCP сервер
mcp = FastMCP("Presentation Builder")


@mcp.tool()
def generate_presentation(config_path: str) -> str:
    """Создать PowerPoint презентацию из JSON конфигурации.

    Этот инструмент принимает путь к JSON файлу с конфигурацией слайдов
    и создаёт PowerPoint презентацию согласно указанным параметрам.

    Args:
        config_path: Абсолютный путь к JSON файлу.

    Supported Layout Types (layout_type):
        - single_wide (1 img, 16:9)
        - single_tall (1 img, 9:16)
        - two_stack (2 imgs, vertical)
        - two_tall_row (2 imgs, horizontal)
        - three_stack (3 imgs, vertical)

    Supported Image Formats:
        - BMP, GIF, JPEG, PNG, TIFF, WMF (native)
        - WebP (auto-converted to PNG)

    Supported Audio Formats:
        - MP3, WAV, M4A and other audio formats
        - Audio is automatically hidden off-slide (not visible)
        - Optional per-slide basis

    Path Resolution:
        - template_path: relative → server dir, absolute → as is
        - output_path: relative → server dir, absolute → as is
        - images: resolved relative to JSON file location
        - audio: resolved relative to JSON file location

    JSON Structure Example:
        {
            "template_path": "template.pptx",
            "layout_name": "ContentLayout",
            "output_path": "output.pptx",
            "slides": [
                {
                    "layout_type": "single_wide",
                    "layout_name": "TitleLayout",
                    "title": "Title Slide",
                    "notes_source": "Cover slide notes",
                    "images": ["cover.jpg"],
                    "audio": "audio/intro.mp3"
                },
                {
                    "layout_type": "single_wide",
                    "title": "Content Slide",
                    "notes_source": "Regular slide notes",
                    "images": ["content.png"]
                },
                {
                    "layout_type": "two_stack",
                    "title": "Slide with Audio",
                    "notes_source": "Slide with voiceover",
                    "images": ["img1.png", "img2.png"],
                    "audio": "audio/voiceover.wav"
                }
            ]
        }

    NEW: Per-Slide Layout Override
        You can now use different PowerPoint layouts in one presentation!
        - Global layout_name: used by default for all slides
        - Per-slide layout_name: overrides global for specific slides

        Example use cases:
        - Title slide + content slides
        - Section dividers + content
        - Different slide styles in one deck

        ⚠️ IMPORTANT: Use ONE template file with MULTIPLE layouts inside!
        The system does NOT support multiple .pptx files due to python-pptx limitations.
        Create TitleLayout, VideoLayout, etc. in the same template file using
        PowerPoint's Slide Master view.

    Returns:
        Сообщение о результате создания презентации с путём к файлу

    Example:
        generate_presentation("C:/projects/my_slides.json")
        -> "✅ Презентация создана: C:/projects/output.pptx\n📊 Создано слайдов: 5"
    """
    logger.info(f"🤖 MCP запрос: generate_presentation")
    logger.debug(f"📋 Путь к конфигурации: {config_path}")
    
    try:
        # Проверяем существование файла
        config_file = Path(config_path).resolve()
        logger.debug(f"🔍 Проверка существования файла: {config_file}")

        if not config_file.exists():
            logger.error(f"❌ Файл конфигурации не найден: {config_file}")
            return (
                f"❌ Ошибка: Файл конфигурации не найден\n"
                f"📁 Путь: {config_file}\n"
                f"💡 Убедитесь что передан правильный абсолютный путь к JSON файлу"
            )

        if not config_file.suffix.lower() == ".json":
            logger.error(f"❌ Неверное расширение файла: {config_path}")
            return f"❌ Ошибка: Файл должен иметь расширение .json: {config_path}"

        # Загружаем конфигурацию
        logger.debug(f"📂 Загрузка конфигурации из {config_file.name}")
        config = ConfigLoader.load(config_file)

        # Проверяем что есть слайды
        if not config.slides:
            logger.error("❌ В конфигурации нет слайдов")
            return "❌ Ошибка: В конфигурации нет слайдов"

        logger.debug(f"📊 Загружено слайдов: {len(config.slides)}")

        # Настройка компонентов
        # ВАЖНО: Для MCP шаблоны ищем в директории сервера, а не JSON!
        server_dir = Path(__file__).parent  # Директория где лежит mcp_server.py
        logger.debug(f"🏠 Директория сервера: {server_dir}")
        
        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)
        registry = LayoutRegistry()
        register_default_layouts(registry)
        logger.debug("🔧 Компоненты инициализированы")

        # Создаём презентацию
        builder = PresentationBuilder(registry, loader, verbose=False)

        # Разрешаем путь к шаблону
        # Если путь относительный - ищем в директории СЕРВЕРА, не JSON!
        template_path_from_config = Path(config.template_path)
        if template_path_from_config.is_absolute():
            template_path = template_path_from_config
        else:
            # Относительный путь - ищем в директории сервера
            template_path = (server_dir / template_path_from_config).resolve()

        logger.debug(f"📄 Путь к шаблону: {template_path}")

        if not template_path.exists():
            logger.error(f"❌ Шаблон не найден: {template_path}")
            return (
                f"❌ Ошибка: Шаблон не найден\n"
                f"📁 Искал здесь: {template_path}\n"
                f"🔍 Указано в JSON: {config.template_path}\n"
                f"🏠 Директория сервера: {server_dir}\n"
                f"💡 Шаблоны должны лежать в директории MCP сервера"
            )

        # Собираем презентацию
        logger.debug(f"🔨 Начало сборки презентации")
        prs = builder.build(config, template_path)

        if prs is None:
            logger.critical("💥 Критическая ошибка при сборке презентации")
            return "❌ Критическая ошибка при сборке презентации"

        # Сохраняем
        # Output тоже разрешаем относительно сервера, если относительный путь
        output_path_from_config = Path(config.output_path)
        if output_path_from_config.is_absolute():
            output_path = output_path_from_config
        else:
            # Относительный путь - сохраняем в директории сервера
            output_path = (server_dir / output_path_from_config).resolve()

        logger.debug(f"💾 Сохранение презентации: {output_path}")
        builder.save(prs, output_path)

        # Проверяем на некритичные ошибки
        errors = builder.get_errors()

        # Формируем ответ
        if errors:
            logger.warning(f"⚠️ Презентация создана с {len(errors)} ошибками")
            # Есть ошибки - показываем их ПОДРОБНО
            error_details = "\n".join([f"  • {err}" for err in errors])
            result = (
                f"⚠️  Презентация создана с ошибками!\n"
                f"📁 Файл: {output_path}\n"
                f"📊 Создано слайдов: {len(config.slides)}\n"
                f"🎨 Макет: {config.layout_name}\n\n"
                f"❌ ОШИБКИ ({len(errors)}):\n{error_details}\n\n"
                f"💡 Проверьте пути к изображениям и правильность конфигурации"
            )
        else:
            # Всё идеально
            logger.info(f"✅ MCP ответ: Успех. Презентация создана: {output_path}")
            result = (
                f"✅ Презентация успешно создана!\n"
                f"📁 Файл: {output_path}\n"
                f"📊 Создано слайдов: {len(config.slides)}\n"
                f"🎨 Макет: {config.layout_name}"
            )

        return result

    except FileNotFoundError as e:
        logger.error(f"❌ MCP ответ: Файл не найден - {e}", exc_info=True)
        return f"❌ Файл не найден: {e}"
    except ValueError as e:
        logger.error(f"❌ MCP ответ: Ошибка в конфигурации - {e}", exc_info=True)
        return f"❌ Ошибка в конфигурации: {e}"
    except PermissionError as e:
        logger.error(f"❌ MCP ответ: Нет прав доступа - {e}", exc_info=True)
        return f"❌ Нет прав доступа: {e}"
    except Exception as e:
        logger.critical(f"💥 MCP ответ: Неожиданная ошибка - {type(e).__name__}: {e}", exc_info=True)
        return f"❌ Неожиданная ошибка: {type(e).__name__}: {e}"


@mcp.tool()
def get_layout_documentation(layout_name: str | None = None) -> str:
    """Получить документацию по макетам презентаций.

    Этот инструмент возвращает подробную документацию о доступных макетах
    для размещения изображений на слайдах. Документация является единым
    источником правды как для людей, так и для AI-агентов.

    Args:
        layout_name: Имя конкретного макета (single_wide, single_tall, two_stack,
                    two_tall_row, three_stack) или None для получения всей документации.
                    Также можно указать "all" для полной документации.

    Returns:
        Markdown-форматированная документация.

    Available Layouts:
        - single_wide: одно широкое изображение (16:9)
        - single_tall: одно высокое изображение (9:16)
        - two_stack: два изображения вертикально
        - two_tall_row: два высоких изображения горизонтально
        - three_stack: три изображения вертикально

    Examples:
        get_layout_documentation("single_wide")  # документация по single_wide
        get_layout_documentation("all")          # вся документация
        get_layout_documentation()               # вся документация (default)
    """
    logger.info(f"📚 MCP запрос: get_layout_documentation({layout_name or 'all'})")
    
    try:
        # Определяем базовую директорию (где находится mcp_server.py)
        base_dir = Path(__file__).parent
        doc_dir = base_dir / "doc"
        layouts_dir = doc_dir / "layouts"
        
        logger.debug(f"📁 Директория документации: {doc_dir}")

        # Доступные макеты
        available_layouts = [
            "single_wide",
            "single_tall",
            "two_stack",
            "two_tall_row",
            "three_stack",
        ]

        # Если запрашивается вся документация или layout_name не указан
        if layout_name is None or layout_name.lower() == "all":
            logger.debug("📖 Запрошена полная документация по всем макетам")
            # Собираем полную документацию
            result = []

            # Сначала добавляем общую информацию
            overview_path = doc_dir / "overview.md"
            if overview_path.exists():
                logger.debug(f"📄 Загрузка overview.md")
                result.append(overview_path.read_text(encoding="utf-8"))
                result.append("\n\n---\n\n")

            # Затем документацию по каждому макету
            result.append("# Детальная документация по макетам\n\n")

            for i, layout in enumerate(available_layouts, 1):
                layout_file = layouts_dir / f"{layout}.md"
                if layout_file.exists():
                    logger.debug(f"📄 Загрузка {layout}.md ({i}/{len(available_layouts)})")
                    result.append(f"\n\n## Макет {i}/{len(available_layouts)}\n\n")
                    result.append(layout_file.read_text(encoding="utf-8"))
                    result.append("\n\n---\n")
                else:
                    logger.warning(f"⚠️ Документация для {layout} не найдена")
                    result.append(f"\n\n⚠️ Документация для `{layout}` не найдена.\n\n")

            logger.info(f"✅ Полная документация собрана ({len(available_layouts)} макетов)")
            return "".join(result)

        # Если запрашивается конкретный макет
        else:
            logger.debug(f"📖 Запрошена документация для макета: {layout_name}")
            
            if layout_name not in available_layouts:
                logger.warning(f"⚠️ Макет '{layout_name}' не найден в списке доступных")
                return (
                    f"❌ Макет '{layout_name}' не найден.\n\n"
                    f"Доступные макеты:\n"
                    + "\n".join([f"  - {layout}" for layout in available_layouts])
                )

            layout_file = layouts_dir / f"{layout_name}.md"

            if not layout_file.exists():
                logger.error(f"❌ Файл документации не найден: {layout_file}")
                return (
                    f"❌ Файл документации для '{layout_name}' не найден: {layout_file}"
                )

            logger.debug(f"📄 Загрузка файла: {layout_file.name}")
            content = layout_file.read_text(encoding="utf-8")
            logger.info(f"✅ Документация для '{layout_name}' загружена успешно")
            return content

    except Exception as e:
        logger.error(f"❌ Ошибка при чтении документации: {type(e).__name__}: {e}", exc_info=True)
        return f"❌ Ошибка при чтении документации: {type(e).__name__}: {e}"


if __name__ == "__main__":
    # Запускаем MCP сервер
    mcp.run()

```

## `models/__init__.py`

```py
"""
Модели данных Auto-Slide.

Этот пакет содержит dataclass-модели для:
- Конфигурации презентации
- Конфигурации слайдов (полиморфные типы)
- Реестра макетов
- Фабрики слайдов
"""

from .config_schema import (
    SlideConfig,
    PresentationConfig,
    validate_config,
)
from .layout_registry import (
    ImagePlacement,
    LayoutBlueprint,
    LayoutRegistry,
)
from .slide_types import (
    BaseSlideConfig,
    ContentSlideConfig,
    YouTubeTitleSlideConfig,
)
from .slide_factory import SlideConfigFactory

__all__ = [
    # Старые классы (обратная совместимость)
    "SlideConfig",
    "PresentationConfig",
    "validate_config",
    # Макеты
    "ImagePlacement",
    "LayoutBlueprint",
    "LayoutRegistry",
    # Новые полиморфные типы слайдов
    "BaseSlideConfig",
    "ContentSlideConfig",
    "YouTubeTitleSlideConfig",
    "SlideConfigFactory",
]

```

## `models/config_schema.py`

```py
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

```

## `models/examples.py`

```py
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

```

## `models/layout_registry.py`

```py
"""
Реестр макетов для презентаций.

Этот модуль определяет структуру макетов слайдов и предоставляет
расширяемый реестр для регистрации и получения макетов.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ImagePlacement:
    """
    Параметры размещения одного изображения на слайде.

    Attributes:
        left: Отступ слева в сантиметрах.
        top: Отступ сверху в сантиметрах.
        max_width: Максимальная ширина изображения в сантиметрах.
        max_height: Максимальная высота изображения в сантиметрах.

    Note:
        При размещении изображения используется "умное" масштабирование:
        изображение вписывается в прямоугольник (max_width x max_height)
        с сохранением пропорций. Один из размеров фиксируется,
        другой вычисляется автоматически.
    """

    left: float  # в см
    top: float  # в см
    max_width: float  # в см
    max_height: float  # в см

    def to_dict(self) -> Dict[str, float]:
        """
        Конвертирует размеры в словарь для дальнейшего использования.

        Returns:
            Словарь с ключами 'left', 'top', 'max_width', 'max_height'
            в сантиметрах (float).

        Note:
            Конвертация в единицы python-pptx (Cm) выполняется в слое бизнес-логики,
            а не в моделях данных.
        """
        return {
            "left": self.left,
            "top": self.top,
            "max_width": self.max_width,
            "max_height": self.max_height,
        }


@dataclass
class LayoutBlueprint:
    """
    Чертёж (blueprint) макета слайда.

    Attributes:
        name: Уникальное имя макета (например, 'single_wide', 'two_stack').
        description: Человекочитаемое описание макета.
        required_images: Ожидаемое количество изображений для этого макета.
        placements: Список параметров размещения для каждого изображения.
                    Длина списка должна соответствовать required_images.

    Example:
        >>> blueprint = LayoutBlueprint(
        ...     name="single_wide",
        ...     description="Одно широкое изображение",
        ...     required_images=1,
        ...     placements=[
        ...         ImagePlacement(left=10.2, top=4.2, max_width=20, max_height=10)
        ...     ]
        ... )
    """

    name: str
    description: str
    required_images: int
    placements: List[ImagePlacement]

    def __post_init__(self):
        """Валидация после инициализации."""
        if len(self.placements) != self.required_images:
            raise ValueError(
                f"Количество placements ({len(self.placements)}) не соответствует "
                f"required_images ({self.required_images}) для макета '{self.name}'"
            )


class LayoutRegistry:
    """
    Расширяемый реестр макетов слайдов.

    Реестр позволяет регистрировать новые макеты и получать их по имени.
    Это обеспечивает расширяемость системы — новые макеты можно добавлять
    без изменения основного кода.

    Example:
        >>> registry = LayoutRegistry()
        >>>
        >>> # Регистрация макета
        >>> single_wide = LayoutBlueprint(
        ...     name="single_wide",
        ...     description="Одно широкое изображение",
        ...     required_images=1,
        ...     placements=[ImagePlacement(10.2, 4.2, 20, 10)]
        ... )
        >>> registry.register(single_wide)
        >>>
        >>> # Получение макета
        >>> layout = registry.get("single_wide")
        >>> print(layout.description)
        Одно широкое изображение
    """

    def __init__(self):
        """Инициализация пустого реестра."""
        self._layouts: Dict[str, LayoutBlueprint] = {}

    def register(self, blueprint: LayoutBlueprint) -> None:
        """
        Регистрирует новый макет в реестре.

        Args:
            blueprint: Чертёж макета для регистрации.

        Raises:
            ValueError: Если макет с таким именем уже зарегистрирован.

        Example:
            >>> registry.register(blueprint)
        """
        if blueprint.name in self._layouts:
            raise ValueError(
                f"Макет с именем '{blueprint.name}' уже зарегистрирован. "
                "Используйте другое имя или сначала удалите существующий макет."
            )

        self._layouts[blueprint.name] = blueprint

    def get(self, name: str) -> LayoutBlueprint:
        """
        Получает макет по имени.

        Args:
            name: Имя макета.

        Returns:
            Чертёж макета.

        Raises:
            KeyError: Если макет с таким именем не найден.

        Example:
            >>> layout = registry.get("single_wide")
        """
        if name not in self._layouts:
            available = ", ".join(self._layouts.keys())
            raise KeyError(
                f"Макет '{name}' не найден в реестре. "
                f"Доступные макеты: {available or '(пусто)'}"
            )

        return self._layouts[name]

    def exists(self, name: str) -> bool:
        """
        Проверяет, зарегистрирован ли макет с данным именем.

        Args:
            name: Имя макета.

        Returns:
            True, если макет существует, иначе False.
        """
        return name in self._layouts

    def list_all(self) -> List[str]:
        """
        Возвращает список имён всех зарегистрированных макетов.

        Returns:
            Список имён макетов.
        """
        return list(self._layouts.keys())

    def unregister(self, name: str) -> None:
        """
        Удаляет макет из реестра.

        Args:
            name: Имя макета для удаления.

        Raises:
            KeyError: Если макет не найден.
        """
        if name not in self._layouts:
            raise KeyError(f"Макет '{name}' не найден в реестре")

        del self._layouts[name]

    def clear(self) -> None:
        """Очищает реестр (удаляет все зарегистрированные макеты)."""
        self._layouts.clear()

```

## `models/slide_factory.py`

```py
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

```

## `models/slide_types.py`

```py
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
        audio: Путь к аудиофайлу для озвучки слайда (опциональное поле)

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
    audio: Optional[str] = None

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
            "audio": self.audio,
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
    REQUIRED_LAYOUT_NAME: ClassVar[str] = (
        "TitleLayout"  # Титульный макет для YouTube слайдов
    )

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

```

## `README.md`

```md
# Presentation Builder# Presentation Builder# Presentation Builder# Presentation Builder

**Автоматизация создания PowerPoint презентаций из структурированных данных****Автоматизация создания PowerPoint презентаций из JSON конфигураций**Автоматизация создания PowerPoint презентаций из JSON конфигураций.**Автоматизация создания PowerPoint презентаций из структурированных данных**

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)## Быстрый старт[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](tests/)

[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](tests/)

---

[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](tests/)

## 🎯 Что это?

---

Модульная система для автоматической генерации PowerPoint презентаций из JSON конфигураций. Устраняет ручной труд по копированию-вставке заголовков, заметок и изображений.

### 1. Установка[![Code style](https://img.shields.io/badge/code%20style-functional-brightgreen.svg)](doc/plan/refactor_plan.md)

### Основная задача

## 🎯 Что это?

Автоматизировать создание однотипных презентаций:

```bash---

- ✅ Заголовки и номера слайдов

- ✅ Заметки докладчика из Markdown файловМодульная система для автоматической генерации PowerPoint презентаций из структурированных JSON конфигураций. Устраняет ручной труд по копированию-вставке заголовков, заметок и изображений.

- ✅ Изображения с автоматическим масштабированием

- ✅ Единый корпоративный стильpip install -r requirements.txt



### Для кого---



- **Преподаватели** — быстрая сборка учебных презентаций```## 📖 Оглавление

- **Создатели контента** — автоматизация видео-презентаций

- **Бизнес** — генерация отчетов и аналитики## 🚀 Быстрый старт

- **Разработчики** — интеграция в CI/CD пайплайны



---

### 1. Установка

## ⚡ Быстрый старт

### 2. Создание конфигурации- [Обзор](#-обзор)

### 1. Установка

```bash

```bash

# Клонируйте репозиторийpip install -r requirements.txt- [Быстрый старт](#-быстрый-старт)

git clone <repository-url>

cd presentation_mcp```



# Установите зависимости`config.json`:- [Возможности](#-возможности)

pip install -r requirements.txt

```### 2. Создайте конфигурацию



### 2. Первая презентация```json- [Архитектура](#-архитектура)



Создайте файл `my_slides.json`:`config.json`:



```json```json{- [Документация](#-документация)

{

  "template_path": "template.pptx",{

  "layout_name": "single_wide",

  "output_path": "result.pptx",  "template_path": "template.pptx",  "template_path": "template.pptx",- [Разработка](#-разработка)

  "slides": [

    {  "layout_name": "VideoLayout",

      "title": "Мой первый слайд",

      "slide_number": "1",  "output_path": "output.pptx",  "layout_name": "VideoLayout",

      "notes_source": "notes.md",

      "images": ["photo.jpg"]  "slides": [

    }

  ]    {  "output_path": "output.pptx",---

}

```      "layout_type": "single_wide",



### 3. Генерация      "title": "Мой первый слайд",  "slides": [



```bash      "notes_source": "notes.md",

python main.py generate --config my_slides.json

```      "images": ["photo.jpg"]    {## 🎯 Обзор



**Готово!** Результат в `result.pptx` 🎉    }



---  ]      "layout_type": "single_wide",



## 📚 Документация}



### 🚀 Начало работы```      "title": "Слайд 1",**Presentation Builder** — это модульная система для автоматической генерации PowerPoint презентаций из JSON конфигураций.



- **[REFERENCE.md](doc/REFERENCE.md)** — полное руководство пользователя

  - Конфигурационные файлы

  - CLI команды### 3. Сгенерируйте презентацию      "notes_source": "notes.md",

  - Пути к файлам

  - Markdown заметки



- **[TEMPLATE_GUIDE.md](doc/TEMPLATE_GUIDE.md)** — создание шаблонов PowerPoint```bash      "images": ["photo.jpg"]### Основная задача

  - Пошаговая инструкция с картинками

  - Работа с Образцом слайдовpython main.py generate --config config.json

  - Заполнители и макеты

  - Анализ существующих шаблонов```    }



### 🤖 Интеграция с AI



- **[MCP_USAGE.md](doc/MCP_USAGE.md)** — использование с AI-агентамиГотово! Результат в `output.pptx` 🎉  ]Устранение ручного труда по копированию-вставке:

  - Настройка Model Context Protocol

  - Интеграция с Cline

  - Автоматическая генерация презентаций

---}

### 📖 Дополнительно



- **[doc/overview.md](doc/overview.md)** — архитектура проекта

- **[doc/samples/](doc/samples/)** — примеры конфигураций## 📋 CLI команды```- Заголовков и номеров слайдов

- **[doc/layouts/](doc/layouts/)** — описание встроенных макетов



---

```bash- Текста заметок докладчика (с поддержкой Markdown)

## 🎨 Возможности

# Генерация презентации

### Гибкая система макетов

python main.py generate --config slides.json [--output result.pptx] [--verbose]### 3. Генерация- Изображений с автоматическим масштабированием

4 встроенных макета + возможность создавать свои:



| Макет | Изображений | Описание |

|-------|-------------|----------|# Анализ шаблона PPTX

| `single_wide` | 1 | Широкое изображение (16:9) |

| `single_tall` | 1 | Высокое изображение (9:16) |python main.py analyze --template template.pptx [--layout "LayoutName"]

| `two_stack` | 2 | Два изображения вертикально |

| `two_tall_row` | 2 | Два высоких рядом |```bash### Для кого это



См. [`doc/layouts/`](doc/layouts/) для деталей.# Справка



### Markdown для заметокpython main.py helppython main.py generate --config config.json



Пишите заметки в Markdown — система автоматически очистит форматирование:```



```markdown```- **Преподаватели**: быстрая сборка учебных презентаций

# Основные пункты

- **Важно**: обратите внимание---

- Второй пункт с *курсивом*

- **Создатели контента**: автоматизация видео-презентаций

> Это будет преобразовано в plain text

```## 📝 Структура JSON



### Умное масштабирование изображений## CLI команды- **Бизнес**: генерация отчетов и аналитики



Автоматическое масштабирование с сохранением пропорций:### Корневая конфигурация



- Анализ размеров изображения- **Разработчики**: интеграция в CI/CD пайплайны

- Подгонка под макет без искажений

- Центрирование в заданных границах| Поле | Тип | Обязательно | Описание |



### Абсолютные и относительные пути|------|-----|-------------|----------|```bash



```json| `template_path` | string | Да | Путь к шаблону PPTX |

{

  "template_path": "C:/Templates/corporate.pptx",| `layout_name` | string | Да | Имя макета из шаблона |# Генерация презентации---

  "slides": [

    {| `output_path` | string | Нет | Путь к выходному файлу (по умолчанию: `output.pptx`) |

      "notes_source": "notes/slide1.md",

      "images": ["../shared/logo.png"]| `slides` | array | Да | Массив слайдов |python main.py generate --config slides.json [--output result.pptx] [--verbose]

    }

  ]

}

```### Конфигурация слайда## 🚀 Быстрый старт



---



## 🛠️ CLI команды| Поле | Тип | Обязательно | Описание |# Анализ шаблона



### Генерация презентации|------|-----|-------------|----------|



```bash| `layout_type` | string | Да | Тип размещения: `single_wide`, `single_tall`, `two_stack`, `two_tall_row` |python main.py analyze --template template.pptx [--layout "LayoutName"]### Установка

python main.py generate --config slides.json --verbose

```| `title` | string | Да | Заголовок слайда |



### Анализ шаблона| `notes_source` | string | Да | Путь к .md файлу ИЛИ inline текст |



```bash| `images` | array | Да | Пути к изображениям (относительные или абсолютные) |

# Список всех макетов

python main.py analyze --template template.pptx# Справка```bash



# Детальный анализ макета---

python main.py analyze --template template.pptx --layout "Blank"

```python main.py help# Клонируйте репозиторий



### Справка## 🎨 Встроенные макеты



```bash```git clone <repository-url>

python main.py help

```| Макет | Изображений | Описание |



---|-------|-------------|----------|cd presentation_mcp



## 📁 Структура проекта| `single_wide` | 1 | Одно широкое изображение (16:9) |



```| `single_tall` | 1 | Одно высокое изображение (9:16) |## Структура JSON

presentation_mcp/

├── main.py                 # CLI точка входа| `two_stack` | 2 | Два изображения вертикально |

├── requirements.txt        # Зависимости

│| `two_tall_row` | 2 | Два высоких изображения рядом |# Установите зависимости

├── config/                 # Настройки и макеты

│   └── settings.py         # Регистрация дефолтных макетов

│

├── core/                   # Бизнес-логика---### Обязательные поляpip install -r requirements.txt

│   ├── presentation_builder.py    # Главный оркестратор

│   ├── markdown_cleaner.py        # Очистка MD → text

│   ├── image_processor.py         # Масштабирование

│   └── template_analyzer.py       # Анализ PPTX## 📂 Примеры```

│

├── models/                 # Модели данных

│   ├── config_schema.py           # SlideConfig, PresentationConfig

│   └── layout_registry.py         # LayoutBlueprint, RegistryСм. [`doc/samples/`](doc/samples/) для готовых примеров:- `template_path` — путь к PPTX шаблону

│

├── io_handlers/            # Работа с файлами

│   ├── path_resolver.py           # Резолюция путей

│   ├── config_loader.py           # Загрузка JSON- **simple_example.json** — базовый пример с одним изображением- `layout_name` — имя макета из шаблона (узнать: `analyze`)### Первая презентация

│   └── resource_loader.py         # Загрузка MD, изображений

│- **multi_image_example.json** — пример с двумя изображениями

├── cli/                    # Командная строка

│   └── commands.py                # generate, analyze, help- **absolute_paths_example.json** — демонстрация абсолютных путей- `slides[]` — массив слайдов

│

├── tests/                  # Тесты (pytest)

│   ├── test_models.py

│   └── test_io_handlers.py---1. **Создайте конфигурацию** (`my_presentation.json`):

│

└── doc/                    # Документация

    ├── REFERENCE.md               # Полное руководство

    ├── TEMPLATE_GUIDE.md          # Создание шаблонов## ✨ Возможности### Поля слайда

    ├── MCP_USAGE.md               # Интеграция с AI

    ├── samples/                   # Примеры конфигураций

    └── layouts/                   # Описание макетов

```### Markdown для заметок```json



---



## 🧪 ТестированиеПишите заметки в Markdown — система автоматически очистит форматирование:- `layout_type` — тип макета (single_wide, single_tall, two_stack, two_tall_row){



```bash

# Все тесты

pytest tests/```markdown- `title` — заголовок слайда  "template_path": "template.pptx",



# С подробным выводом# Основные пункты

pytest tests/ -v

- `notes_source` — путь к .md файлу ИЛИ inline текст  "layout_name": "single_wide",

# С покрытием кода

pytest tests/ --cov=models --cov=core --cov=io_handlers- **Важно**: обратите внимание

```

- Второй пункт с *курсивом*- `images[]` — массив путей к изображениям  "output_path": "result.pptx",

---

## 🔧 Расширение

> Это будет преобразовано в plain text  "slides": [

### Добавление своего макета

```

**1. Создайте шаблон** (см. [TEMPLATE_GUIDE.md](doc/TEMPLATE_GUIDE.md))

## Встроенные макеты    {

**2. Проанализируйте его:**

### Умное масштабирование изображений

```bash

python main.py analyze --template template.pptx --layout "MyLayout"      "title": "Мой первый слайд",

```

Автоматическое масштабирование с сохранением пропорций — изображения всегда вписываются в макет без искажений.

**3. Зарегистрируйте в `config/settings.py`:**

- **single_wide** — 1 широкое изображение (16:9)      "slide_number": "1",

```python

my_layout = LayoutBlueprint(### Абсолютные и относительные пути

    name="my_custom",

    placeholders={- **single_tall** — 1 высокое изображение (9:16)      "notes_source": "notes.md",

        "TITLE": 0,

        "NUMBER": 1```json

    },

    image_placements=[{- **two_stack** — 2 изображения вертикально      "images": ["photo.jpg"]

        ImagePlacement(

            placeholder_idx=10,  "template_path": "C:/Templates/corporate.pptx",  // абсолютный

            left=Inches(1),

            top=Inches(2),  "slides": [- **two_tall_row** — 2 высоких изображения рядом    }

            width=Inches(4),

            height=Inches(3)    {

        )

    ]      "notes_source": "notes/slide1.md",  // относительно JSON  ]

)

      "images": ["../shared/logo.png"]     // относительно JSON

registry.register(my_layout)

```    }## Примеры}



**4. Используйте в JSON:**  ]



```json}```

{

  "layout_name": "my_custom",```

  ...

}См. `doc/samples/` для примеров конфигураций.

```

---

---

2. **Запустите генерацию**:

## 📦 Зависимости

## 🏗️ Архитектура

- **python-pptx** — работа с PowerPoint

- **Pillow** — обработка изображений## Документация

- **markdown** — парсинг Markdown

- **beautifulsoup4** — очистка HTML```

- **pytest** — тестирование (dev)

presentation_mcp/```bash

---

├── main.py              # CLI точка входа

## 🎓 История проекта

├── requirements.txt     # Зависимости- **REFERENCE.md** — полная справка по всем возможностямpython main.py generate --config my_presentation.json

Проект начался как 3 монолитных скрипта и был полностью рефакторен в модульную архитектуру:

├── config/              # Настройки и регистрация макетов

- ✅ 5 пакетов с чётким разделением ответственности

- ✅ 24+ unit тестов с pytest├── core/                # Бизнес-логика (builder, cleaner, analyzer)```

- ✅ CLI интерфейс с 3 командами

- ✅ Полная документация├── models/              # Модели данных (config_schema, layout_registry)

---├── io_handlers/         # Работа с файлами (loader, resolver)## Тесты

## 🗺️ Roadmap├── cli/                 # CLI команды (generate, analyze, help)

### Планируется├── tests/               # Unit тесты с pytest3. **Откройте результат**: `result.pptx` 🎉

- [ ] Поддержка таблиц в слайдах└── doc/                 # Документация и примеры

- [ ] Темы оформления (light/dark)

- [ ] Экспорт в PDF    ├── samples/         # Примеры конфигураций```bash

- [ ] Web UI для создания конфигураций

- [ ] Шаблоны для популярных форматов (Notion, Confluence)    └── REFERENCE.md     # Полная справка

### В разработке```pytest tests/### Примеры

- [x] MCP интеграция для AI-агентов

- [x] WebP поддержка изображений

- [x] Автоматическая конвертация форматов### Принципы проектирования```

---

## 🤝 Участие в проекте- **SRP**: каждый модуль — одна ответственностьСм. готовые примеры в [`doc/samples/`](samples/)

1. Fork репозитория- **DRY**: переиспользуемые компоненты

2. Создайте feature branch (`git checkout -b feature/amazing`)

3. Commit изменений (`git commit -m 'Add amazing feature'`)- **YAGNI**: только необходимая функциональность## Структура проекта

4. Push в branch (`git push origin feature/amazing`)

5. Откройте Pull Request- **Функциональный стиль**: pure functions где возможно

---- `simple_example.json` — базовый пример

## 📄 Лицензия---

MIT License — используйте свободно в своих проектах.```- `multi_image_example.json` — несколько изображений

---## 🧪 Тестирование

## 💡 Полезные ссылки├── main.py              # CLI точка входа- `absolute_paths_example.json` — абсолютные пути

- **Документация:**```bash

  - [Полное руководство](doc/REFERENCE.md)

  - [Создание шаблонов](doc/TEMPLATE_GUIDE.md)# Запуск всех тестов├── config/              # Настройки и макеты

  - [MCP интеграция](doc/MCP_USAGE.md)

pytest tests/

- **Примеры:**

  - [Примеры конфигураций](doc/samples/)├── core/                # Бизнес-логика---

  - [Описание макетов](doc/layouts/)

# С подробным выводом

- **Разработка:**

  - [Архитектура проекта](doc/overview.md)pytest tests/ -v├── models/              # Модели данных

  - [Тесты](tests/)

---

# С покрытием кода├── io_handlers/         # Работа с файлами## ✨ Возможности

**Создано с ❤️ для автоматизации рутины**

pytest tests/ --cov=models --cov=core --cov=io_handlers

**Есть вопросы?** Изучите [REFERENCE.md](doc/REFERENCE.md) или создайте Issue.

```├── cli/                 # CLI команды



---├── tests/               # Unit тесты### 🎨 Гибкая система макетов



## 📚 Документация└── doc/samples/         # Примеры конфигураций



- **REFERENCE.md** — полная справка по всем возможностям```4 встроенных макета + возможность добавлять свои:

- **doc/samples/** — примеры конфигураций и заметок

- **Docstrings в коде** — документация модулей и функций

- **single_wide** — одно широкое изображение (16:9)

---- **single_tall** — одно высокое изображение (9:16)

- **two_stack** — два изображения вертикально

## 🔧 Расширение функциональности- **two_tall_row** — два высоких изображения рядом



### Добавление нового макета### 📝 Markdown для заметок



1. Создайте `LayoutBlueprint` в `config/settings.py`Пишите заметки в Markdown — система автоматически очистит форматирование:

2. Зарегистрируйте его в `register_default_layouts()`

3. Используйте в JSON через `layout_type````markdown

# Основные пункты

См. [`config/settings.py`](config/settings.py) для примеров.

- **Важно**: обратите внимание

---- Второй пункт с *курсивом*



## 📦 Зависимости> Это будет преобразовано в plain text

```

- **python-pptx** — работа с PowerPoint

- **Pillow** — обработка изображений### 🖼️ Умное масштабирование изображений

- **markdown** — парсинг Markdown

- **beautifulsoup4** — очистка HTMLАвтоматическое масштабирование с сохранением пропорций:

- **pytest** — тестирование (dev)

- Анализ размеров изображения (Pillow)

---- Подгонка под макет без искажений

- Центрирование в заданных границах

## 🎓 История проекта

### 🛣️ Абсолютные и относительные пути

Проект начался как 3 монолитных скрипта и был полностью рефакторен в модульную архитектуру:

```json

- ✅ 5 пакетов с чётким разделением ответственности{

- ✅ 24+ unit тестов с pytest  "template_path": "C:/Templates/corporate.pptx",  // абсолютный

- ✅ CLI интерфейс с 3 командами  "slides": [

- ✅ Полная документация    {

      "notes_source": "notes/slide1.md",  // относительно JSON

---      "images": ["../shared/logo.png"]    // относительно JSON

    }

## 🤝 Вклад  ]

}

1. Fork репозитория```

2. Создайте feature branch

3. Commit изменений### 🎯 CLI интерфейс

4. Push в branch

5. Откройте Pull Request```bash

# Генерация презентации

---python main.py generate --config slides.json --verbose



**Создано с ❤️ для автоматизации рутины**# Анализ шаблона

python main.py analyze --template template.pptx --layout "Blank"

# Справка
python main.py help
```

### ✅ Полное тестовое покрытие

- Unit тесты с pytest
- Тестирование моделей, IO handlers, core логики
- 24+ тестовых случая

---

## 🏗️ Архитектура

Система построена на принципах **SRP**, **DRY**, **YAGNI** с функциональным стилем.

### Структура проекта

```
presentation_mcp/
├── main.py              # CLI точка входа
├── config/              # Настройки и регистрация макетов
│   ├── settings.py      # Дефолтные макеты
│   └── __init__.py
├── core/                # Бизнес-логика
│   ├── presentation_builder.py    # Главный оркестратор
│   ├── markdown_cleaner.py        # Очистка MD → text
│   ├── image_processor.py         # Масштабирование изображений
│   ├── template_analyzer.py       # Анализ PPTX шаблонов
│   └── __init__.py
├── models/              # Модели данных
│   ├── config_schema.py          # SlideConfig, PresentationConfig
│   ├── layout_registry.py        # LayoutBlueprint, Registry
│   ├── examples.py               # Примеры использования
│   └── __init__.py
├── io_handlers/         # Работа с файлами
│   ├── path_resolver.py         # Резолюция путей
│   ├── config_loader.py         # Загрузка JSON
│   ├── resource_loader.py       # Загрузка MD, изображений
│   └── __init__.py
├── cli/                 # Командная строка
│   ├── commands.py              # generate, analyze, help
│   └── __init__.py
├── tests/               # Тесты (pytest)
│   ├── test_models.py
│   ├── test_io_handlers.py
│   ├── conftest.py
│   └── README.md
└── doc/                 # Документация
    ├── USAGE.md                 # Полное руководство
    ├── MIGRATION.md             # Миграция со старой версии
    ├── samples/                 # Примеры конфигураций
    └── plan/                    # План рефакторинга
```

### Ключевые компоненты

#### 1. **Models** — типобезопасные данные

```python
@dataclass
class SlideConfig:
    """Конфигурация одного слайда"""
    title: str = ""
    slide_number: str = ""
    notes_source: str = ""  # MD файл или inline текст
    images: List[str] = field(default_factory=list)
```

#### 2. **LayoutRegistry** — расширяемая система макетов

```python
registry = get_layout_registry()
registry.register(custom_layout)
layout = registry.get("single_wide")
```

#### 3. **PresentationBuilder** — оркестратор сборки

```python
builder = PresentationBuilder(config, registry, verbose=True)
builder.build()
builder.save("output.pptx")
```

#### 4. **PathResolver** — умная работа с путями

```python
resolver = PathResolver(json_location="/path/to/config.json")
full_path = resolver.resolve("images/photo.jpg")
# → /path/to/images/photo.jpg
```

### Принципы проектирования

- **SRP**: каждый модуль — одна ответственность
- **DRY**: переиспользуемые компоненты
- **YAGNI**: только необходимая функциональность
- **Функциональный стиль**: pure functions где возможно
- **Dependency Injection**: для тестируемости

---

## 📚 Документация

- **[USAGE.md](USAGE.md)** — полное руководство пользователя
- **[MIGRATION.md](MIGRATION.md)** — миграция со старой версии
- **[refactor_plan.md](plan/refactor_plan.md)** — план рефакторинга (10 этапов)
- **[tests/README.md](../tests/README.md)** — документация по тестам
- **[samples/](samples/)** — примеры конфигураций

### Полезные команды

```bash
# Генерация с подробным выводом
python main.py generate --config config.json --verbose

# Анализ всех макетов в шаблоне
python main.py analyze --template template.pptx

# Анализ конкретного макета
python main.py analyze --template template.pptx --layout "Blank"

# Запуск тестов
pytest tests/

# Запуск тестов с покрытием
pytest tests/ --cov=models --cov=core --cov=io_handlers
```

---

## 🔧 Разработка

### Установка dev окружения

```bash
pip install -r requirements.txt
pip install pytest pytest-cov  # для тестов
```

### Запуск тестов

```bash
# Все тесты
pytest tests/

# Конкретный модуль
pytest tests/test_models.py

# С подробным выводом
pytest tests/ -v

# С покрытием кода
pytest tests/ --cov=models --cov=core --cov=io_handlers
```

### Добавление нового макета

1. **Создайте LayoutBlueprint** в `config/settings.py`:

```python
my_layout = LayoutBlueprint(
    name="my_custom",
    placeholders={
        "TITLE": 0,
        "NUMBER": 1,
        "IMAGE_1": 10
    },
    image_placements=[
        ImagePlacement(
            placeholder_idx=10,
            left=Inches(1),
            top=Inches(2),
            width=Inches(8),
            height=Inches(5)
        )
    ]
)
```

2. **Зарегистрируйте** в `register_default_layouts()`:

```python
registry.register(my_layout)
```

3. **Используйте** в JSON:

```json
{
  "layout_name": "my_custom",
  ...
}
```

### Расширение функциональности

- **Новые типы заметок**: расширьте `ResourceLoader.load_notes()`
- **Новые форматы изображений**: расширьте `image_processor.py`
- **Новые команды CLI**: добавьте в `cli/commands.py`
- **Валидация**: расширьте `models/config_schema.py`

---

## 🎓 История проекта

Проект начался как набор из трех монолитных скриптов:

- `one.py` — анализатор шаблонов
- `two.py` — очиститель Markdown
- `three.py` — генератор презентаций

В результате рефакторинга (10 этапов, ~210 минут) система была преобразована в:

- **5 пакетов** с четким разделением ответственности
- **24+ unit теста** с pytest
- **CLI интерфейс** с 3 командами
- **Полная документация** и примеры

Детали рефакторинга: [`doc/plan/refactor_plan.md`](plan/refactor_plan.md)

---

## 📦 Зависимости

- **python-pptx** — работа с PowerPoint
- **Pillow** — обработка изображений
- **markdown** — парсинг Markdown
- **beautifulsoup4** — очистка HTML
- **pytest** — тестирование (dev)

```bash
pip install -r requirements.txt
```

---

## 🤝 Вклад

Проект открыт для улучшений:

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменений (`git commit -m 'Добавлена amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

---

## 📄 Лицензия

Этот проект создан в учебных и демонстрационных целях.

---

## 🎯 Roadmap

### Завершено ✅

- [x] Модульная архитектура
- [x] Поддержка Markdown
- [x] CLI интерфейс
- [x] Unit тесты
- [x] Документация

### В планах 🔮

- [ ] Поддержка таблиц в слайдах
- [ ] Batch обработка нескольких конфигураций
- [ ] Web интерфейс
- [ ] Интеграция с ИИ для генерации контента
- [ ] Экспорт в другие форматы (PDF, HTML)

---

**Создано с ❤️ для автоматизации рутины**

```

## `requirements.txt`

```txt
ÿþ#   P r e s e n t a t i o n   B u i l d e r   -   D e p e n d e n c i e s 
 
 
 
 #   C o r e   p r e s e n t a t i o n   l i b r a r y 
 
 p y t h o n - p p t x = = 1 . 0 . 2 
 
 
 
 #   I m a g e   p r o c e s s i n g 
 
 p i l l o w = = 1 2 . 0 . 0 
 
 
 
 #   M a r k d o w n   s u p p o r t 
 
 M a r k d o w n = = 3 . 1 0 
 
 b e a u t i f u l s o u p 4 = = 4 . 1 4 . 2 
 
 l x m l = = 6 . 0 . 2 
 
 s o u p s i e v e = = 2 . 8 
 
 
 
 #   T y p e   h i n t s   s u p p o r t 
 
 t y p i n g _ e x t e n s i o n s = = 4 . 1 5 . 0 
 
 
 
 #   O p t i o n a l :   f o r   a d d i t i o n a l   f e a t u r e s 
 
 x l s x w r i t e r = = 3 . 2 . 9 
 
 
 
 #   M C P   S e r v e r   s u p p o r t 
 
 m c p > = 1 . 0 . 0 
 
 
 
 #   D e v e l o p m e n t   d e p e n d e n c i e s   ( o p t i o n a l ) 
 
 #   p y t e s t = = 8 . 0 . 0 
 
 #   p y t e s t - c o v = = 4 . 1 . 0 
 
 
 
 
```

## `templates/README.md`

```md
# PowerPoint Шаблоны

Эта папка содержит все PowerPoint шаблоны для генерации презентаций.

---

## 📋 Доступные шаблоны

### 1. `youtube_base.pptx` (Базовый)

**Назначение:** Стандартный шаблон для создания YouTube презентаций без титульного слайда.

**Содержит макеты:**
- `ContentLayout` — основной макет для контентных слайдов

**Когда использовать:**
- Презентации без обложки
- Продолжение существующей серии видео
- Простые слайд-шоу

**Пример конфигурации:**
```json
{
  "template_path": "templates/youtube_base.pptx",
  "layout_name": "ContentLayout",
  "slides": [
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Введение",
      "notes_source": "notes.md",
      "images": ["screenshot.png"]
    }
  ]
}
```

---

### 2. `youtube_title.pptx` (С титульным слайдом)

**Назначение:** Расширенный шаблон для презентаций с титульной обложкой.

**Содержит макеты:**
- `TitleLayout` — макет для титульного слайда (обложка видео)
- `ContentLayout` — основной макет для контентных слайдов

**Особенности TitleLayout:**
- Заголовок (крупный шрифт, по центру)
- Подзаголовок
- Номер в серии (опционально)
- Квадратная обложка

**Когда использовать:**
- Новая серия видео (нужна обложка)
- Курсы с нумерацией уроков
- Презентации с брендированной обложкой

**Пример конфигурации:**
```json
{
  "template_path": "templates/youtube_title.pptx",
  "layout_name": "ContentLayout",
  "slides": [
    {
      "slide_type": "title_youtube",
      "title": "Основы Python",
      "subtitle": "Полное руководство для начинающих",
      "series_number": "Часть 1",
      "images": ["cover_square.jpg"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Введение",
      "notes_source": "notes.md",
      "images": ["intro.png"]
    }
  ]
}
```

---

## 🎨 Структура placeholder'ов

### ContentLayout
- **idx=0**: Заголовок слайда
- **idx=1**: Номер слайда

### TitleLayout
- **idx=0**: Заголовок (title)
- **idx=1**: Номер слайда
- **idx=2**: Подзаголовок (subtitle)
- **idx=3**: Номер в серии (series_number)

---

## 🔧 Создание собственного шаблона

1. Откройте один из существующих шаблонов в PowerPoint
2. Перейдите в **"Вид"** → **"Образец слайдов"**
3. Создайте или измените макет
4. Сохраните под новым именем в этой папке
5. Обновите документацию здесь

См. [TEMPLATE_GUIDE.md](../doc/TEMPLATE_GUIDE.md) для подробной инструкции.

---

## 📚 Дополнительные ресурсы

- **[TEMPLATE_GUIDE.md](../doc/TEMPLATE_GUIDE.md)** — пошаговое создание шаблонов
- **[REFERENCE.md](../doc/REFERENCE.md)** — полная документация
- **[doc/samples/](../doc/samples/)** — примеры конфигураций

```

## `tests/__init__.py`

```py
"""
Тесты для проекта Auto-Slide.

Этот пакет содержит unit и интеграционные тесты для всех компонентов.
"""

```

## `tests/conftest.py`

```py
"""
Конфигурация для pytest.

Этот файл содержит fixtures и настройки для всех тестов.
"""

import pytest


@pytest.fixture
def sample_slide_config():
    """Фикстура: образец конфигурации слайда."""
    from models import SlideConfig

    return SlideConfig(
        layout_type="single_wide",
        title="Test Slide",
        notes_source="Test notes",
        images=["test.png"],
    )


@pytest.fixture
def sample_presentation_config(sample_slide_config):
    """Фикстура: образец конфигурации презентации."""
    from models import PresentationConfig

    return PresentationConfig(
        slides=[sample_slide_config],
        template_path="template.pptx",
        output_path="output.pptx",
    )


@pytest.fixture
def layout_registry_with_defaults():
    """Фикстура: реестр с зарегистрированными макетами по умолчанию."""
    from models import LayoutRegistry
    from config import register_default_layouts

    registry = LayoutRegistry()
    register_default_layouts(registry)

    return registry

```

## `tests/test_bytesio_integration.py`

```py
"""
Интеграционный тест для проверки работы с BytesIO при конвертации WebP.

Этот скрипт проверяет, что:
1. convert_webp_to_png возвращает BytesIO объект
2. BytesIO содержит валидные PNG данные
3. Временные файлы на диске не создаются
"""

import io
from pathlib import Path
from core.image_processor import convert_webp_to_png
from PIL import Image


def test_bytesio_conversion():
    """Проверка, что конвертация возвращает BytesIO."""
    print("🔍 Тест: Проверка возвращаемого типа...")

    # Создаем простое WebP изображение для теста
    test_dir = Path(__file__).parent / "test_data"
    test_webp = test_dir / "test_image.webp"

    if not test_webp.exists():
        print(f"⚠️  Тестовое изображение не найдено: {test_webp}")
        print("   Создаем тестовое WebP изображение...")
        test_dir.mkdir(exist_ok=True)

        # Создаем простое тестовое изображение
        img = Image.new("RGB", (100, 100), color="red")
        img.save(test_webp, "WEBP")
        print(f"✅ Создано: {test_webp}")

    # Тестируем конвертацию
    result = convert_webp_to_png(test_webp)

    # Проверка 1: Это BytesIO?
    assert isinstance(result, io.BytesIO), (
        f"❌ Ожидался BytesIO, получен {type(result)}"
    )
    print("✅ Тип возвращаемого значения: BytesIO")

    # Проверка 2: Можем ли мы прочитать PNG из буфера?
    result.seek(0)  # Сброс на начало
    test_img = Image.open(result)
    assert test_img.format == "PNG", f"❌ Ожидался PNG, получен {test_img.format}"
    print(f"✅ Формат изображения в буфере: {test_img.format}")
    print(f"✅ Размер изображения: {test_img.size}")

    # Проверка 3: Буфер не пуст?
    result.seek(0, 2)  # Переход в конец
    buffer_size = result.tell()
    assert buffer_size > 0, "❌ Буфер пустой!"
    print(f"✅ Размер буфера: {buffer_size} байт")

    # Проверка 4: Временные файлы не создаются?
    temp_files = list(test_dir.glob("*.png"))
    if temp_files:
        print(f"⚠️  Обнаружены PNG файлы в тестовой директории: {temp_files}")
        print("   (Это может быть остатки от старых тестов)")
    else:
        print("✅ Временные PNG файлы НЕ созданы на диске")

    print("\n🎉 Все проверки пройдены! Конвертация работает через BytesIO.")


if __name__ == "__main__":
    test_bytesio_conversion()

```

## `tests/test_data/task.md`

```md
Тестовая презентация про установку VS Code

## Обложка

images/cover.png
Заголовок
Подзаголовок
Номер 1

## Слайд 1

images/1_1.png
images/1_2.png
Позиция два горизонтальных один под одним

Тайтл слайда "Загрузка VS Code"
Текст для начитки напиши сам

## Слайд 2

images/2_1.png
images/2_2.png
Позиция два вертикальных рядом
Тайтл: Как открыть проект?
Текст для начитки напиши сам

```

## `tests/test_data/test_slides_config.json`

```json
{
  "template_path": "templates/youtube_base.pptx",
  "output_path": "tests/test_data/test_output.pptx",
  "layout_name": "VideoLayout",
  "slides": [
    {
      "slide_type": "title_youtube",
      "layout_type": "single_wide",
      "layout_name": "TitleLayout",
      "title": "Установка Visual Studio Code",
      "subtitle": "Полное руководство для начинающих",
      "series_number": "Урок #1",
      "notes_source": "Обложка презентации о том, как установить VS Code - лучший редактор кода с открытым исходным кодом.",
      "images": ["images/cover.webp"]
    },
    {
      "layout_type": "two_stack",
      "title": "Шаг 1: Скачивание VS Code",
      "notes_source": "Переходим на официальный сайт code.visualstudio.com и скачиваем установщик для Windows. Доступны версии для разных платформ.",
      "images": ["images/1_1.webp", "images/1_2.webp"],
      "audio": "images/test_audio.mp3"
    },
    {
      "layout_type": "two_tall_row",
      "title": "Шаг 2: Открытие папки проекта",
      "notes_source": "После установки открываем VS Code и выбираем папку с проектом через меню File > Open Folder или через контекстное меню Windows.",
      "images": ["images/2_1.webp", "images/2_2.webp"]
    },
    {
      "layout_type": "single_wide",
      "title": "Bonus: GIF тест",
      "notes_source": "Проверяем что GIF-файлы корректно вставляются в презентацию. VS Code - мощный инструмент для разработки!",
      "images": ["images/test_gif.gif"]
    }
  ]
}

```

## `tests/test_io_handlers.py`

```py
"""
Unit тесты для IO handlers.

Тестирует PathResolver, ConfigLoader, ResourceLoader.
"""

import pytest
import json
from pathlib import Path
from io_handlers import PathResolver, ConfigLoader, ResourceLoader


class TestPathResolver:
    """Тесты для PathResolver."""

    def test_resolve_relative_path(self, tmp_path):
        """Разрешение относительного пути."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        resolver = PathResolver(config_file)

        # Относительный путь должен разрешиться относительно config_file
        resolved = resolver.resolve("images/test.png")
        expected = tmp_path / "images" / "test.png"

        assert resolved == expected

    def test_resolve_absolute_path(self, tmp_path):
        """Разрешение абсолютного пути."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        resolver = PathResolver(config_file)

        absolute_path = Path("C:/absolute/path.png")
        resolved = resolver.resolve(absolute_path)

        assert resolved == absolute_path.resolve()

    def test_resolve_nonexistent_config_raises_error(self):
        """Несуществующий config должен вызывать ошибку."""
        with pytest.raises(ValueError, match="не найден"):
            PathResolver(Path("nonexistent.json"))

    def test_config_path_must_be_file(self, tmp_path):
        """Config path должен быть файлом, а не директорией."""
        with pytest.raises(ValueError, match="должен указывать на файл"):
            PathResolver(tmp_path)


class TestConfigLoader:
    """Тесты для ConfigLoader."""

    def test_load_valid_config(self, tmp_path):
        """Загрузка валидной конфигурации."""
        config_file = tmp_path / "config.json"
        config_data = {
            "slides": [
                {
                    "layout_type": "single_wide",
                    "title": "Test",
                    "notes_source": "notes",
                    "images": ["image.png"],
                }
            ]
        }
        config_file.write_text(json.dumps(config_data))

        config = ConfigLoader.load(config_file)

        assert len(config.slides) == 1
        assert config.slides[0].title == "Test"

    def test_load_nonexistent_file_raises_error(self):
        """Несуществующий файл - ошибка."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load(Path("nonexistent.json"))

    def test_load_invalid_json_raises_error(self, tmp_path):
        """Невалидный JSON - ошибка."""
        config_file = tmp_path / "bad.json"
        config_file.write_text("{invalid json")

        with pytest.raises(json.JSONDecodeError):
            ConfigLoader.load(config_file)

    def test_legacy_notes_text_support(self, tmp_path):
        """Поддержка legacy поля notes_text."""
        config_file = tmp_path / "config.json"
        config_data = {
            "slides": [
                {
                    "layout_type": "single_wide",
                    "title": "Test",
                    "notes_text": "Legacy notes",  # Старое поле
                    "images": [],
                }
            ]
        }
        config_file.write_text(json.dumps(config_data))

        config = ConfigLoader.load(config_file)

        # notes_text должен конвертироваться в notes_source
        assert config.slides[0].notes_source == "Legacy notes"


class TestResourceLoader:
    """Тесты для ResourceLoader."""

    def test_load_notes_from_md_file(self, tmp_path):
        """Загрузка заметок из MD файла."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        md_file = tmp_path / "notes.md"
        md_file.write_text("# Test Markdown\n\nContent")

        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)

        notes = loader.load_notes("notes.md")

        assert "Test Markdown" in notes
        assert "Content" in notes

    def test_load_notes_inline_text(self, tmp_path):
        """Загрузка inline заметок (не из файла)."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)

        notes = loader.load_notes("Inline notes text")

        assert notes == "Inline notes text"

    def test_load_notes_nonexistent_md_raises_error(self, tmp_path):
        """Несуществующий MD файл - ошибка."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)

        with pytest.raises(FileNotFoundError):
            loader.load_notes("nonexistent.md")

    def test_resolve_image(self, tmp_path):
        """Разрешение пути к изображению."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        image_file = tmp_path / "image.png"
        image_file.write_text("fake image")

        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)

        resolved = loader.resolve_image("image.png")

        assert resolved == image_file

    def test_resolve_nonexistent_image_raises_error(self, tmp_path):
        """Несуществующее изображение - ошибка."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)

        with pytest.raises(FileNotFoundError):
            loader.resolve_image("nonexistent.png")

```

## `tests/test_models.py`

```py
"""
Unit тесты для моделей данных.

Тестирует SlideConfig, PresentationConfig, LayoutRegistry.
"""

import pytest
from models import (
    SlideConfig,
    PresentationConfig,
    validate_config,
    ImagePlacement,
    LayoutBlueprint,
    LayoutRegistry,
)
from models.slide_types import (
    BaseSlideConfig,
    ContentSlideConfig,
    YouTubeTitleSlideConfig,
)
from models.slide_factory import SlideConfigFactory


class TestSlideConfig:
    """Тесты для SlideConfig."""

    def test_create_valid_slide(self):
        """Создание валидного слайда."""
        slide = SlideConfig(
            layout_type="single_wide",
            title="Test Slide",
            notes_source="Test notes",
            images=["image1.png"],
        )

        assert slide.layout_type == "single_wide"
        assert slide.title == "Test Slide"
        assert slide.notes_source == "Test notes"
        assert len(slide.images) == 1
        assert slide.layout_name is None  # По умолчанию None

    def test_slide_with_layout_override(self):
        """Создание слайда с переопределением макета."""
        slide = SlideConfig(
            layout_type="single_wide",
            title="Title Slide",
            notes_source="Cover notes",
            images=["cover.jpg"],
            layout_name="TitleLayout",
        )

        assert slide.layout_name == "TitleLayout"
        assert slide.layout_type == "single_wide"

    def test_empty_title_raises_error(self):
        """Пустой заголовок должен вызывать ошибку."""
        with pytest.raises(ValueError, match="title не может быть пустым"):
            SlideConfig(
                layout_type="single_wide", title="", notes_source="notes", images=[]
            )

    def test_empty_layout_type_raises_error(self):
        """Пустой layout_type должен вызывать ошибку."""
        with pytest.raises(ValueError, match="layout_type не может быть пустым"):
            SlideConfig(layout_type="", title="Title", notes_source="notes", images=[])

    def test_default_images_list(self):
        """По умолчанию images - пустой список."""
        slide = SlideConfig(
            layout_type="single_wide", title="Title", notes_source="notes"
        )

        assert slide.images == []


class TestPresentationConfig:
    """Тесты для PresentationConfig."""

    def test_create_valid_config(self):
        """Создание валидной конфигурации."""
        slide = SlideConfig(
            layout_type="single_wide", title="Slide 1", notes_source="notes", images=[]
        )

        config = PresentationConfig(
            slides=[slide], template_path="template.pptx", output_path="output.pptx"
        )

        assert len(config.slides) == 1
        assert config.template_path == "template.pptx"
        assert config.output_path == "output.pptx"

    def test_empty_slides_raises_error(self):
        """Пустой список слайдов должен вызывать ошибку."""
        with pytest.raises(ValueError, match="slides не может быть пустым"):
            PresentationConfig(slides=[])

    def test_dict_to_slideconfig_conversion(self):
        """Автоконвертация словарей в BaseSlideConfig через фабрику."""
        config = PresentationConfig(
            slides=[
                {
                    "slide_type": "content",
                    "layout_type": "single_wide",
                    "title": "Title",
                    "notes_source": "notes",
                    "images": [],
                }
            ]
        )

        assert isinstance(config.slides[0], ContentSlideConfig)
        assert config.slides[0].title == "Title"


class TestValidateConfig:
    """Тесты для validate_config."""

    def test_duplicate_titles_warning(self):
        """Дублирующиеся заголовки должны давать предупреждение."""
        config = PresentationConfig(
            slides=[
                SlideConfig("single_wide", "Same Title", "notes", []),
                SlideConfig("single_wide", "Same Title", "notes", []),
            ]
        )

        warnings = validate_config(config)

        assert len(warnings) > 0
        assert any("Same Title" in w for w in warnings)

    def test_slide_without_images_warning(self):
        """Слайд без изображений должен давать предупреждение."""
        config = PresentationConfig(
            slides=[
                SlideConfig("single_wide", "Title", "notes", []),
            ]
        )

        warnings = validate_config(config)

        assert len(warnings) > 0
        assert any("не содержит изображений" in w for w in warnings)


class TestImagePlacement:
    """Тесты для ImagePlacement."""

    def test_create_placement(self):
        """Создание размещения изображения."""
        placement = ImagePlacement(left=10.0, top=5.0, max_width=20.0, max_height=10.0)

        assert placement.left == 10.0
        assert placement.top == 5.0
        assert placement.max_width == 20.0
        assert placement.max_height == 10.0

    def test_to_dict(self):
        """Конвертация в словарь."""
        placement = ImagePlacement(10.0, 5.0, 20.0, 10.0)
        d = placement.to_dict()

        assert d["left"] == 10.0
        assert d["top"] == 5.0
        assert d["max_width"] == 20.0
        assert d["max_height"] == 10.0


class TestLayoutBlueprint:
    """Тесты для LayoutBlueprint."""

    def test_create_blueprint(self):
        """Создание чертежа макета."""
        blueprint = LayoutBlueprint(
            name="test_layout",
            description="Test",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )

        assert blueprint.name == "test_layout"
        assert blueprint.required_images == 1
        assert len(blueprint.placements) == 1

    def test_mismatch_placements_raises_error(self):
        """Несовпадение placements и required_images - ошибка."""
        with pytest.raises(ValueError, match="Количество placements"):
            LayoutBlueprint(
                name="bad_layout",
                description="Bad",
                required_images=2,
                placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
            )


class TestLayoutRegistry:
    """Тесты для LayoutRegistry."""

    def test_register_and_get_layout(self):
        """Регистрация и получение макета."""
        registry = LayoutRegistry()
        blueprint = LayoutBlueprint(
            name="test",
            description="Test",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )

        registry.register(blueprint)
        retrieved = registry.get("test")

        assert retrieved.name == "test"

    def test_duplicate_registration_raises_error(self):
        """Повторная регистрация макета - ошибка."""
        registry = LayoutRegistry()
        blueprint = LayoutBlueprint(
            name="test",
            description="Test",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )

        registry.register(blueprint)

        with pytest.raises(ValueError, match="уже зарегистрирован"):
            registry.register(blueprint)

    def test_get_nonexistent_layout_raises_error(self):
        """Получение несуществующего макета - ошибка."""
        registry = LayoutRegistry()

        with pytest.raises(KeyError, match="не найден"):
            registry.get("nonexistent")

    def test_exists(self):
        """Проверка существования макета."""
        registry = LayoutRegistry()
        blueprint = LayoutBlueprint(
            name="test",
            description="Test",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )

        assert not registry.exists("test")
        registry.register(blueprint)
        assert registry.exists("test")

    def test_list_all(self):
        """Получение списка всех макетов."""
        registry = LayoutRegistry()
        blueprint1 = LayoutBlueprint(
            name="layout1",
            description="L1",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )
        blueprint2 = LayoutBlueprint(
            name="layout2",
            description="L2",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )

        registry.register(blueprint1)
        registry.register(blueprint2)

        all_layouts = registry.list_all()

        assert len(all_layouts) == 2
        assert "layout1" in all_layouts
        assert "layout2" in all_layouts


class TestContentSlideConfig:
    """Тесты для ContentSlideConfig."""

    def test_create_valid_content_slide(self):
        """Создание валидного контентного слайда."""
        slide = ContentSlideConfig(
            layout_type="single_wide",
            title="Test Content",
            notes_source="notes.md",
            images=["img1.png"],
        )

        assert slide.SLIDE_TYPE == "content"
        assert slide.layout_type == "single_wide"
        assert slide.title == "Test Content"
        assert slide.images == ["img1.png"]

    def test_content_slide_to_dict(self):
        """Сериализация ContentSlideConfig в dict."""
        slide = ContentSlideConfig(
            layout_type="two_stack",
            title="My Slide",
            notes_source="text",
            images=["a.png", "b.png"],
            layout_name="VideoLayout",
        )

        d = slide.to_dict()

        assert d["slide_type"] == "content"
        assert d["layout_type"] == "two_stack"
        assert d["title"] == "My Slide"
        assert d["layout_name"] == "VideoLayout"
        assert len(d["images"]) == 2

    def test_content_slide_missing_layout_type(self):
        """Отсутствие layout_type вызывает ошибку."""
        with pytest.raises(ValueError, match="layout_type не может быть пустым"):
            ContentSlideConfig(
                layout_type="", title="Title", notes_source="notes", images=[]
            )


class TestYouTubeTitleSlideConfig:
    """Тесты для YouTubeTitleSlideConfig."""

    def test_create_valid_youtube_title(self):
        """Создание валидного титульного слайда YouTube."""
        slide = YouTubeTitleSlideConfig(
            layout_type="title_youtube",  # Указываем фиксированный layout_type
            title="Мой канал",
            subtitle="Видео о Python",
            notes_source="intro.md",
            images=["logo.png"],
        )

        assert slide.SLIDE_TYPE == "title_youtube"
        assert slide.title == "Мой канал"
        assert slide.subtitle == "Видео о Python"
        assert slide.series_number is None
        assert slide.images == ["logo.png"]
        assert slide.layout_name == "TitleLayout"  # Автоматически установлен

    def test_youtube_title_with_series_number(self):
        """Титульный слайд с номером серии."""
        slide = YouTubeTitleSlideConfig(
            layout_type="title_youtube",
            title="Название канала",
            subtitle="Описание серии",
            series_number="Часть 3",
            notes_source="notes",
            images=["logo.png"],
        )

        assert slide.series_number == "Часть 3"

    def test_youtube_title_missing_subtitle(self):
        """Отсутствие subtitle вызывает ошибку."""
        with pytest.raises(ValueError, match="subtitle"):
            YouTubeTitleSlideConfig(
                layout_type="title_youtube",
                title="Channel",
                subtitle="",
                notes_source="notes",
                images=["logo.png"],
            )

    def test_youtube_title_to_dict(self):
        """Сериализация YouTubeTitleSlideConfig в dict."""
        slide = YouTubeTitleSlideConfig(
            layout_type="title_youtube",
            title="Test Channel",
            subtitle="Episode description",
            series_number="Part 1",
            notes_source="my_notes.md",
            images=["channel_logo.webp"],
        )

        d = slide.to_dict()

        assert d["slide_type"] == "title_youtube"
        assert d["title"] == "Test Channel"
        assert d["subtitle"] == "Episode description"
        assert d["series_number"] == "Part 1"
        assert d["layout_name"] == "TitleLayout"
        assert d["images"] == ["channel_logo.webp"]


class TestSlideConfigFactory:
    """Тесты для SlideConfigFactory."""

    def test_factory_create_content_slide(self):
        """Фабрика создаёт ContentSlideConfig из dict."""
        data = {
            "slide_type": "content",
            "layout_type": "single_wide",
            "title": "Test",
            "notes_source": "notes.md",
            "images": ["img.png"],
        }

        slide = SlideConfigFactory.create(data)

        assert isinstance(slide, ContentSlideConfig)
        assert slide.layout_type == "single_wide"
        assert slide.title == "Test"

    def test_factory_create_youtube_title(self):
        """Фабрика создаёт YouTubeTitleSlideConfig из dict."""
        data = {
            "slide_type": "title_youtube",
            "layout_type": "title_youtube",
            "title": "My Channel",
            "subtitle": "Cool videos",
            "notes_source": "intro",
            "images": ["logo.jpg"],
        }

        slide = SlideConfigFactory.create(data)

        assert isinstance(slide, YouTubeTitleSlideConfig)
        assert slide.title == "My Channel"
        assert slide.subtitle == "Cool videos"

    def test_factory_unknown_slide_type(self):
        """Неизвестный slide_type вызывает ошибку."""
        data = {
            "slide_type": "unknown_type",
            "title": "Test",
        }

        with pytest.raises(ValueError, match="Неизвестный slide_type"):
            SlideConfigFactory.create(data)

    def test_factory_missing_slide_type(self):
        """Отсутствие slide_type создаёт ContentSlideConfig по умолчанию."""
        data = {
            "layout_type": "single_wide",
            "title": "Test",
            "notes_source": "notes",
        }

        slide = SlideConfigFactory.create(data)

        assert isinstance(slide, ContentSlideConfig)
        assert slide.SLIDE_TYPE == "content"

    def test_factory_get_registered_types(self):
        """Получение списка зарегистрированных типов."""
        types = SlideConfigFactory.get_registered_types()

        assert "content" in types
        assert "title_youtube" in types
        assert len(types) >= 2

```

