"""
Unit тесты для моделей данных.

Тестирует SlideConfig, PresentationConfig, LayoutRegistry.
"""

import pytest
from models import (
    SlideConfig,
    PresentationConfig,
    validate_config,
    ImagePlacement,
    LayoutBlueprint,
    LayoutRegistry,
)
from models.slide_types import (
    BaseSlideConfig,
    ContentSlideConfig,
    YouTubeTitleSlideConfig,
)
from models.slide_factory import SlideConfigFactory


class TestSlideConfig:
    """Тесты для SlideConfig."""

    def test_create_valid_slide(self):
        """Создание валидного слайда."""
        slide = SlideConfig(
            layout_type="single_wide",
            title="Test Slide",
            notes_source="Test notes",
            images=["image1.png"],
        )

        assert slide.layout_type == "single_wide"
        assert slide.title == "Test Slide"
        assert slide.notes_source == "Test notes"
        assert len(slide.images) == 1
        assert slide.layout_name is None  # По умолчанию None

    def test_slide_with_layout_override(self):
        """Создание слайда с переопределением макета."""
        slide = SlideConfig(
            layout_type="single_wide",
            title="Title Slide",
            notes_source="Cover notes",
            images=["cover.jpg"],
            layout_name="TitleLayout",
        )

        assert slide.layout_name == "TitleLayout"
        assert slide.layout_type == "single_wide"

    def test_empty_title_raises_error(self):
        """Пустой заголовок должен вызывать ошибку."""
        with pytest.raises(ValueError, match="title не может быть пустым"):
            SlideConfig(
                layout_type="single_wide", title="", notes_source="notes", images=[]
            )

    def test_empty_layout_type_raises_error(self):
        """Пустой layout_type должен вызывать ошибку."""
        with pytest.raises(ValueError, match="layout_type не может быть пустым"):
            SlideConfig(layout_type="", title="Title", notes_source="notes", images=[])

    def test_default_images_list(self):
        """По умолчанию images - пустой список."""
        slide = SlideConfig(
            layout_type="single_wide", title="Title", notes_source="notes"
        )

        assert slide.images == []


class TestPresentationConfig:
    """Тесты для PresentationConfig."""

    def test_create_valid_config(self):
        """Создание валидной конфигурации."""
        slide = SlideConfig(
            layout_type="single_wide", title="Slide 1", notes_source="notes", images=[]
        )

        config = PresentationConfig(
            slides=[slide], template_path="template.pptx", output_path="output.pptx"
        )

        assert len(config.slides) == 1
        assert config.template_path == "template.pptx"
        assert config.output_path == "output.pptx"

    def test_empty_slides_raises_error(self):
        """Пустой список слайдов должен вызывать ошибку."""
        with pytest.raises(ValueError, match="slides не может быть пустым"):
            PresentationConfig(slides=[])

    def test_dict_to_slideconfig_conversion(self):
        """Автоконвертация словарей в BaseSlideConfig через фабрику."""
        config = PresentationConfig(
            slides=[
                {
                    "slide_type": "content",
                    "layout_type": "single_wide",
                    "title": "Title",
                    "notes_source": "notes",
                    "images": [],
                }
            ]
        )

        assert isinstance(config.slides[0], ContentSlideConfig)
        assert config.slides[0].title == "Title"


class TestValidateConfig:
    """Тесты для validate_config."""

    def test_duplicate_titles_warning(self):
        """Дублирующиеся заголовки должны давать предупреждение."""
        config = PresentationConfig(
            slides=[
                SlideConfig("single_wide", "Same Title", "notes", []),
                SlideConfig("single_wide", "Same Title", "notes", []),
            ]
        )

        warnings = validate_config(config)

        assert len(warnings) > 0
        assert any("Same Title" in w for w in warnings)

    def test_slide_without_images_warning(self):
        """Слайд без изображений должен давать предупреждение."""
        config = PresentationConfig(
            slides=[
                SlideConfig("single_wide", "Title", "notes", []),
            ]
        )

        warnings = validate_config(config)

        assert len(warnings) > 0
        assert any("не содержит изображений" in w for w in warnings)


class TestImagePlacement:
    """Тесты для ImagePlacement."""

    def test_create_placement(self):
        """Создание размещения изображения."""
        placement = ImagePlacement(left=10.0, top=5.0, max_width=20.0, max_height=10.0)

        assert placement.left == 10.0
        assert placement.top == 5.0
        assert placement.max_width == 20.0
        assert placement.max_height == 10.0

    def test_to_dict(self):
        """Конвертация в словарь."""
        placement = ImagePlacement(10.0, 5.0, 20.0, 10.0)
        d = placement.to_dict()

        assert d["left"] == 10.0
        assert d["top"] == 5.0
        assert d["max_width"] == 20.0
        assert d["max_height"] == 10.0


class TestLayoutBlueprint:
    """Тесты для LayoutBlueprint."""

    def test_create_blueprint(self):
        """Создание чертежа макета."""
        blueprint = LayoutBlueprint(
            name="test_layout",
            description="Test",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )

        assert blueprint.name == "test_layout"
        assert blueprint.required_images == 1
        assert len(blueprint.placements) == 1

    def test_mismatch_placements_raises_error(self):
        """Несовпадение placements и required_images - ошибка."""
        with pytest.raises(ValueError, match="Количество placements"):
            LayoutBlueprint(
                name="bad_layout",
                description="Bad",
                required_images=2,
                placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
            )


class TestLayoutRegistry:
    """Тесты для LayoutRegistry."""

    def test_register_and_get_layout(self):
        """Регистрация и получение макета."""
        registry = LayoutRegistry()
        blueprint = LayoutBlueprint(
            name="test",
            description="Test",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )

        registry.register(blueprint)
        retrieved = registry.get("test")

        assert retrieved.name == "test"

    def test_duplicate_registration_raises_error(self):
        """Повторная регистрация макета - ошибка."""
        registry = LayoutRegistry()
        blueprint = LayoutBlueprint(
            name="test",
            description="Test",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )

        registry.register(blueprint)

        with pytest.raises(ValueError, match="уже зарегистрирован"):
            registry.register(blueprint)

    def test_get_nonexistent_layout_raises_error(self):
        """Получение несуществующего макета - ошибка."""
        registry = LayoutRegistry()

        with pytest.raises(KeyError, match="не найден"):
            registry.get("nonexistent")

    def test_exists(self):
        """Проверка существования макета."""
        registry = LayoutRegistry()
        blueprint = LayoutBlueprint(
            name="test",
            description="Test",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )

        assert not registry.exists("test")
        registry.register(blueprint)
        assert registry.exists("test")

    def test_list_all(self):
        """Получение списка всех макетов."""
        registry = LayoutRegistry()
        blueprint1 = LayoutBlueprint(
            name="layout1",
            description="L1",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )
        blueprint2 = LayoutBlueprint(
            name="layout2",
            description="L2",
            required_images=1,
            placements=[ImagePlacement(10.0, 5.0, 20.0, 10.0)],
        )

        registry.register(blueprint1)
        registry.register(blueprint2)

        all_layouts = registry.list_all()

        assert len(all_layouts) == 2
        assert "layout1" in all_layouts
        assert "layout2" in all_layouts


class TestContentSlideConfig:
    """Тесты для ContentSlideConfig."""

    def test_create_valid_content_slide(self):
        """Создание валидного контентного слайда."""
        slide = ContentSlideConfig(
            layout_type="single_wide",
            title="Test Content",
            notes_source="notes.md",
            images=["img1.png"],
        )

        assert slide.SLIDE_TYPE == "content"
        assert slide.layout_type == "single_wide"
        assert slide.title == "Test Content"
        assert slide.images == ["img1.png"]

    def test_content_slide_to_dict(self):
        """Сериализация ContentSlideConfig в dict."""
        slide = ContentSlideConfig(
            layout_type="two_stack",
            title="My Slide",
            notes_source="text",
            images=["a.png", "b.png"],
            layout_name="VideoLayout",
        )

        d = slide.to_dict()

        assert d["slide_type"] == "content"
        assert d["layout_type"] == "two_stack"
        assert d["title"] == "My Slide"
        assert d["layout_name"] == "VideoLayout"
        assert len(d["images"]) == 2

    def test_content_slide_missing_layout_type(self):
        """Отсутствие layout_type вызывает ошибку."""
        with pytest.raises(ValueError, match="layout_type не может быть пустым"):
            ContentSlideConfig(
                layout_type="", title="Title", notes_source="notes", images=[]
            )


class TestYouTubeTitleSlideConfig:
    """Тесты для YouTubeTitleSlideConfig."""

    def test_create_valid_youtube_title(self):
        """Создание валидного титульного слайда YouTube."""
        slide = YouTubeTitleSlideConfig(
            layout_type="title_youtube",  # Указываем фиксированный layout_type
            title="Мой канал",
            subtitle="Видео о Python",
            notes_source="intro.md",
            images=["logo.png"],
        )

        assert slide.SLIDE_TYPE == "title_youtube"
        assert slide.title == "Мой канал"
        assert slide.subtitle == "Видео о Python"
        assert slide.series_number is None
        assert slide.images == ["logo.png"]
        assert slide.layout_name == "TitleLayout"  # Автоматически установлен

    def test_youtube_title_with_series_number(self):
        """Титульный слайд с номером серии."""
        slide = YouTubeTitleSlideConfig(
            layout_type="title_youtube",
            title="Название канала",
            subtitle="Описание серии",
            series_number="Часть 3",
            notes_source="notes",
            images=["logo.png"],
        )

        assert slide.series_number == "Часть 3"

    def test_youtube_title_missing_subtitle(self):
        """Отсутствие subtitle вызывает ошибку."""
        with pytest.raises(ValueError, match="subtitle"):
            YouTubeTitleSlideConfig(
                layout_type="title_youtube",
                title="Channel",
                subtitle="",
                notes_source="notes",
                images=["logo.png"],
            )

    def test_youtube_title_to_dict(self):
        """Сериализация YouTubeTitleSlideConfig в dict."""
        slide = YouTubeTitleSlideConfig(
            layout_type="title_youtube",
            title="Test Channel",
            subtitle="Episode description",
            series_number="Part 1",
            notes_source="my_notes.md",
            images=["channel_logo.webp"],
        )

        d = slide.to_dict()

        assert d["slide_type"] == "title_youtube"
        assert d["title"] == "Test Channel"
        assert d["subtitle"] == "Episode description"
        assert d["series_number"] == "Part 1"
        assert d["layout_name"] == "TitleLayout"
        assert d["images"] == ["channel_logo.webp"]


class TestSlideConfigFactory:
    """Тесты для SlideConfigFactory."""

    def test_factory_create_content_slide(self):
        """Фабрика создаёт ContentSlideConfig из dict."""
        data = {
            "slide_type": "content",
            "layout_type": "single_wide",
            "title": "Test",
            "notes_source": "notes.md",
            "images": ["img.png"],
        }

        slide = SlideConfigFactory.create(data)

        assert isinstance(slide, ContentSlideConfig)
        assert slide.layout_type == "single_wide"
        assert slide.title == "Test"

    def test_factory_create_youtube_title(self):
        """Фабрика создаёт YouTubeTitleSlideConfig из dict."""
        data = {
            "slide_type": "title_youtube",
            "layout_type": "title_youtube",
            "title": "My Channel",
            "subtitle": "Cool videos",
            "notes_source": "intro",
            "images": ["logo.jpg"],
        }

        slide = SlideConfigFactory.create(data)

        assert isinstance(slide, YouTubeTitleSlideConfig)
        assert slide.title == "My Channel"
        assert slide.subtitle == "Cool videos"

    def test_factory_unknown_slide_type(self):
        """Неизвестный slide_type вызывает ошибку."""
        data = {
            "slide_type": "unknown_type",
            "title": "Test",
        }

        with pytest.raises(ValueError, match="Неизвестный slide_type"):
            SlideConfigFactory.create(data)

    def test_factory_missing_slide_type(self):
        """Отсутствие slide_type создаёт ContentSlideConfig по умолчанию."""
        data = {
            "layout_type": "single_wide",
            "title": "Test",
            "notes_source": "notes",
        }

        slide = SlideConfigFactory.create(data)

        assert isinstance(slide, ContentSlideConfig)
        assert slide.SLIDE_TYPE == "content"

    def test_factory_get_registered_types(self):
        """Получение списка зарегистрированных типов."""
        types = SlideConfigFactory.get_registered_types()

        assert "content" in types
        assert "title_youtube" in types
        assert len(types) >= 2
