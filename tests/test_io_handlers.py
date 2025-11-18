"""
Unit тесты для IO handlers.

Тестирует PathResolver, ConfigLoader, ResourceLoader.
"""

import pytest
import json
from pathlib import Path
from io_handlers import PathResolver, ConfigLoader, ResourceLoader


class TestPathResolver:
    """Тесты для PathResolver."""
    
    def test_resolve_relative_path(self, tmp_path):
        """Разрешение относительного пути."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        
        resolver = PathResolver(config_file)
        
        # Относительный путь должен разрешиться относительно config_file
        resolved = resolver.resolve("images/test.png")
        expected = tmp_path / "images" / "test.png"
        
        assert resolved == expected
    
    def test_resolve_absolute_path(self, tmp_path):
        """Разрешение абсолютного пути."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        
        resolver = PathResolver(config_file)
        
        absolute_path = Path("C:/absolute/path.png")
        resolved = resolver.resolve(absolute_path)
        
        assert resolved == absolute_path.resolve()
    
    def test_resolve_nonexistent_config_raises_error(self):
        """Несуществующий config должен вызывать ошибку."""
        with pytest.raises(ValueError, match="не найден"):
            PathResolver(Path("nonexistent.json"))
    
    def test_config_path_must_be_file(self, tmp_path):
        """Config path должен быть файлом, а не директорией."""
        with pytest.raises(ValueError, match="должен указывать на файл"):
            PathResolver(tmp_path)


class TestConfigLoader:
    """Тесты для ConfigLoader."""
    
    def test_load_valid_config(self, tmp_path):
        """Загрузка валидной конфигурации."""
        config_file = tmp_path / "config.json"
        config_data = {
            "slides": [
                {
                    "layout_type": "single_wide",
                    "title": "Test",
                    "notes_source": "notes",
                    "images": ["image.png"]
                }
            ]
        }
        config_file.write_text(json.dumps(config_data))
        
        config = ConfigLoader.load(config_file)
        
        assert len(config.slides) == 1
        assert config.slides[0].title == "Test"
    
    def test_load_nonexistent_file_raises_error(self):
        """Несуществующий файл - ошибка."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load(Path("nonexistent.json"))
    
    def test_load_invalid_json_raises_error(self, tmp_path):
        """Невалидный JSON - ошибка."""
        config_file = tmp_path / "bad.json"
        config_file.write_text("{invalid json")
        
        with pytest.raises(json.JSONDecodeError):
            ConfigLoader.load(config_file)
    
    def test_legacy_notes_text_support(self, tmp_path):
        """Поддержка legacy поля notes_text."""
        config_file = tmp_path / "config.json"
        config_data = {
            "slides": [
                {
                    "layout_type": "single_wide",
                    "title": "Test",
                    "notes_text": "Legacy notes",  # Старое поле
                    "images": []
                }
            ]
        }
        config_file.write_text(json.dumps(config_data))
        
        config = ConfigLoader.load(config_file)
        
        # notes_text должен конвертироваться в notes_source
        assert config.slides[0].notes_source == "Legacy notes"


class TestResourceLoader:
    """Тесты для ResourceLoader."""
    
    def test_load_notes_from_md_file(self, tmp_path):
        """Загрузка заметок из MD файла."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        
        md_file = tmp_path / "notes.md"
        md_file.write_text("# Test Markdown\n\nContent")
        
        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)
        
        notes = loader.load_notes("notes.md")
        
        assert "Test Markdown" in notes
        assert "Content" in notes
    
    def test_load_notes_inline_text(self, tmp_path):
        """Загрузка inline заметок (не из файла)."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        
        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)
        
        notes = loader.load_notes("Inline notes text")
        
        assert notes == "Inline notes text"
    
    def test_load_notes_nonexistent_md_raises_error(self, tmp_path):
        """Несуществующий MD файл - ошибка."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        
        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)
        
        with pytest.raises(FileNotFoundError):
            loader.load_notes("nonexistent.md")
    
    def test_resolve_image(self, tmp_path):
        """Разрешение пути к изображению."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        
        image_file = tmp_path / "image.png"
        image_file.write_text("fake image")
        
        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)
        
        resolved = loader.resolve_image("image.png")
        
        assert resolved == image_file
    
    def test_resolve_nonexistent_image_raises_error(self, tmp_path):
        """Несуществующее изображение - ошибка."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        
        resolver = PathResolver(config_file)
        loader = ResourceLoader(resolver)
        
        with pytest.raises(FileNotFoundError):
            loader.resolve_image("nonexistent.png")
