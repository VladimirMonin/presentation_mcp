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
