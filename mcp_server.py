#!/usr/bin/env python3
"""
MCP Server для Presentation Builder

Предоставляет инструмент для создания PowerPoint презентаций
через Model Context Protocol.
"""

from mcp.server.fastmcp import FastMCP
from pathlib import Path
from models import LayoutRegistry
from io_handlers import ConfigLoader, PathResolver, ResourceLoader
from core import PresentationBuilder
from config import register_default_layouts

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

    Supported Image Formats:
        - BMP, GIF, JPEG, PNG, TIFF, WMF (native)
        - WebP (auto-converted to PNG)

    Path Resolution:
        - template_path: relative → server dir, absolute → as is
        - output_path: relative → server dir, absolute → as is
        - images: resolved relative to JSON file location

    JSON Structure Example:
        {
            "template_path": "template.pptx",
            "layout_name": "VideoLayout",
            "output_path": "output.pptx",
            "slides": [
                {
                    "layout_type": "single_wide",
                    "title": "Slide Title",
                    "notes_source": "Notes text or path to .md",
                    "images": ["C:/abs/path/image.png"]
                }
            ]
        }
        
    Returns:
        Сообщение о результате создания презентации с путём к файлу
        
    Example:
        generate_presentation("C:/projects/my_slides.json")
        -> "✅ Презентация создана: C:/projects/output.pptx\n📊 Создано слайдов: 5"
    """
    try:
        # Проверяем существование файла
        config_file = Path(config_path).resolve()
        
        if not config_file.exists():
            return (
                f"❌ Ошибка: Файл конфигурации не найден\n"
                f"📁 Путь: {config_file}\n"
                f"💡 Убедитесь что передан правильный абсолютный путь к JSON файлу"
            )
        
        if not config_file.suffix.lower() == '.json':
            return f"❌ Ошибка: Файл должен иметь расширение .json: {config_path}"
        
        # Загружаем конфигурацию
        config = ConfigLoader.load(config_file)
        
        # Проверяем что есть слайды
        if not config.slides:
            return "❌ Ошибка: В конфигурации нет слайдов"
        
        # Настройка компонентов
        # ВАЖНО: Для MCP шаблоны ищем в директории сервера, а не JSON!
        server_dir = Path(__file__).parent  # Директория где лежит mcp_server.py
        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)
        registry = LayoutRegistry()
        register_default_layouts(registry)
        
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
        
        if not template_path.exists():
            return (
                f"❌ Ошибка: Шаблон не найден\n"
                f"📁 Искал здесь: {template_path}\n"
                f"🔍 Указано в JSON: {config.template_path}\n"
                f"� Директория сервера: {server_dir}\n"
                f"💡 Шаблоны должны лежать в директории MCP сервера"
            )
        
        # Собираем презентацию
        prs = builder.build(config, template_path)
        
        if prs is None:
            return "❌ Критическая ошибка при сборке презентации"
        
        # Сохраняем
        # Output тоже разрешаем относительно сервера, если относительный путь
        output_path_from_config = Path(config.output_path)
        if output_path_from_config.is_absolute():
            output_path = output_path_from_config
        else:
            # Относительный путь - сохраняем в директории сервера
            output_path = (server_dir / output_path_from_config).resolve()
        
        builder.save(prs, output_path)
        
        # Проверяем на некритичные ошибки
        errors = builder.get_errors()
        
        # Формируем ответ
        if errors:
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
            result = (
                f"✅ Презентация успешно создана!\n"
                f"📁 Файл: {output_path}\n"
                f"📊 Создано слайдов: {len(config.slides)}\n"
                f"🎨 Макет: {config.layout_name}"
            )
        
        return result
        
    except FileNotFoundError as e:
        return f"❌ Файл не найден: {e}"
    except ValueError as e:
        return f"❌ Ошибка в конфигурации: {e}"
    except PermissionError as e:
        return f"❌ Нет прав доступа: {e}"
    except Exception as e:
        return f"❌ Неожиданная ошибка: {type(e).__name__}: {e}"


if __name__ == "__main__":
    # Запускаем MCP сервер
    mcp.run()
