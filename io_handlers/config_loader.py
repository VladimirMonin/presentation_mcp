"""
Загрузка и валидация JSON конфигураций.

Этот модуль отвечает за чтение JSON файлов и преобразование их
в типизированные dataclass объекты.
"""

import json
from pathlib import Path
from typing import Union, Dict, Any

from models import PresentationConfig, SlideConfig


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
        
        if not json_path.exists():
            raise FileNotFoundError(
                f"Конфигурационный файл не найден: {json_path}"
            )
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Ошибка парсинга JSON в {json_path}: {e.msg}",
                e.doc,
                e.pos
            )
        
        return ConfigLoader._parse_config(data, json_path)
    
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
            # Извлекаем слайды
            slides_data = data.get("slides", [])
            if not isinstance(slides_data, list):
                raise ValueError("Поле 'slides' должно быть массивом")
            
            # Парсим слайды
            slides = []
            for i, slide_data in enumerate(slides_data, 1):
                try:
                    slide = ConfigLoader._parse_slide(slide_data)
                    slides.append(slide)
                except Exception as e:
                    raise ValueError(
                        f"Ошибка в слайде #{i}: {e}"
                    ) from e
            
            # Создаём конфигурацию
            config = PresentationConfig(
                template_path=data.get("template_path", "template.pptx"),
                output_path=data.get("output_path", "output.pptx"),
                layout_name=data.get("layout_name", "VideoLayout"),
                slides=slides
            )
            
            return config
            
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Ошибка при парсинге конфигурации из {source_path}: {e}"
            ) from e
    
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
            images=data.get("images", [])
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
        
        data = {
            "template_path": config.template_path,
            "output_path": config.output_path,
            "layout_name": config.layout_name,
            "slides": [
                {
                    "layout_type": slide.layout_type,
                    "title": slide.title,
                    "notes_source": slide.notes_source,
                    "images": slide.images,
                }
                for slide in config.slides
            ]
        }
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
