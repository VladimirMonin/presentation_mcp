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
