"""
Загрузка ресурсов (Markdown файлов, изображений).

Этот модуль обеспечивает единообразную загрузку всех внешних ресурсов,
необходимых для генерации презентации.
"""

from pathlib import Path

from .path_resolver import PathResolver


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
            md_path = self.resolver.resolve_and_check(source)

            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return content
            except IOError as e:
                raise IOError(f"Ошибка чтения Markdown файла {md_path}: {e}") from e
        else:
            # Это inline текст
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
        return self.resolver.resolve_and_check(image_path)

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
        return self.resolver.resolve_and_check(audio_path)

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
        try:
            self.resolver.resolve_and_check(path)
            return True
        except FileNotFoundError:
            return False
