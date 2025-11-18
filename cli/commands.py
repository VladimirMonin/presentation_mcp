"""
CLI команды для Auto-Slide.

Этот модуль содержит команды командной строки для генерации
презентаций и анализа шаблонов.
"""

from pathlib import Path
from typing import Optional

from models import LayoutRegistry
from io_handlers import PathResolver, ConfigLoader, ResourceLoader
from core import PresentationBuilder, analyze_template
from config import register_default_layouts


def cmd_generate(
    config_path: str,
    output: Optional[str] = None,
    template: Optional[str] = None,
    verbose: bool = True
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
    try:
        # Шаг 1: Загрузка конфигурации
        config_path_obj = Path(config_path).resolve()
        
        if not config_path_obj.exists():
            print(f"✗ Ошибка: Файл конфигурации не найден: {config_path}")
            return 1
        
        if verbose:
            print(f"📖 Загрузка конфигурации: {config_path_obj.name}")
        
        config = ConfigLoader.load(config_path_obj)
        
        # Применение переопределений из CLI
        if output:
            config.output_path = output
        if template:
            config.template_path = template
        
        # Шаг 2: Настройка компонентов
        resolver = PathResolver(config_path_obj)
        loader = ResourceLoader(resolver)
        registry = LayoutRegistry()
        register_default_layouts(registry)
        
        # Шаг 3: Сборка презентации
        builder = PresentationBuilder(registry, loader, verbose=verbose)
        
        template_path = resolver.resolve(config.template_path)
        
        if not template_path.exists():
            print(f"✗ Ошибка: Шаблон не найден: {template_path}")
            return 1
        
        prs = builder.build(config, template_path)
        
        if prs is None:
            print("✗ Критическая ошибка при сборке презентации")
            return 1
        
        # Шаг 4: Сохранение
        output_path = resolver.resolve(config.output_path)
        builder.save(prs, output_path)
        
        # Проверка на ошибки
        errors = builder.get_errors()
        if errors:
            print(f"\n⚠ Завершено с {len(errors)} некритичными ошибками")
            return 2  # Частичный успех
        
        return 0  # Полный успех
        
    except FileNotFoundError as e:
        print(f"✗ Ошибка: Файл не найден: {e}")
        return 1
    except ValueError as e:
        print(f"✗ Ошибка валидации: {e}")
        return 1
    except Exception as e:
        print(f"✗ Неожиданная ошибка: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_analyze(
    template_path: str,
    layout: str = "VideoLayout",
    list_only: bool = False
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
    try:
        template_path_obj = Path(template_path).resolve()
        
        if not template_path_obj.exists():
            print(f"✗ Ошибка: Файл не найден: {template_path}")
            return 1
        
        if list_only:
            from core import list_layouts
            list_layouts(template_path_obj)
        else:
            analyze_template(template_path_obj, layout)
        
        return 0
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return 1


def cmd_help() -> None:
    """Выводит справку по использованию CLI."""
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
    if not args or args[0] in ['help', '--help', '-h']:
        cmd_help()
        return 0
    
    command = args[0]
    
    if command == 'generate':
        if len(args) < 2:
            print("✗ Ошибка: Не указан файл конфигурации")
            print("Использование: python main.py generate <config.json> [опции]")
            return 1
        
        config_path = args[1]
        output = None
        template = None
        verbose = True
        
        # Парсинг опций
        i = 2
        while i < len(args):
            if args[i] in ['-o', '--output'] and i + 1 < len(args):
                output = args[i + 1]
                i += 2
            elif args[i] in ['-t', '--template'] and i + 1 < len(args):
                template = args[i + 1]
                i += 2
            elif args[i] in ['-q', '--quiet']:
                verbose = False
                i += 1
            else:
                print(f"⚠ Неизвестная опция: {args[i]}")
                i += 1
        
        return cmd_generate(config_path, output, template, verbose)
    
    elif command == 'analyze':
        if len(args) < 2:
            print("✗ Ошибка: Не указан файл шаблона")
            print("Использование: python main.py analyze <template.pptx> [опции]")
            return 1
        
        template_path = args[1]
        layout = "VideoLayout"
        list_only = False
        
        # Парсинг опций
        i = 2
        while i < len(args):
            if args[i] in ['-l', '--layout'] and i + 1 < len(args):
                layout = args[i + 1]
                i += 2
            elif args[i] == '--list':
                list_only = True
                i += 1
            else:
                print(f"⚠ Неизвестная опция: {args[i]}")
                i += 1
        
        return cmd_analyze(template_path, layout, list_only)
    
    else:
        print(f"✗ Неизвестная команда: {command}")
        print("Используйте 'python main.py help' для справки")
        return 1
