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
