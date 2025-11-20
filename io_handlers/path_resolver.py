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
