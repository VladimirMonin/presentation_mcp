"""
Модуль размещения контента на слайдах.

Классы-стратегии для размещения различных типов контента:
- ImagePlacer: Размещение изображений
- MediaPlacer: Размещение аудио/видео
"""

from .image_placer import ImagePlacer
from .media_placer import MediaPlacer

__all__ = ["ImagePlacer", "MediaPlacer"]
