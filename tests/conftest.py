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
