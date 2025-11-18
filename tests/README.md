# Auto-Slide Tests

Этот каталог содержит тесты для проекта Auto-Slide.

## Структура

- `test_models.py` - Тесты для моделей данных (SlideConfig, PresentationConfig, LayoutRegistry)
- `test_io_handlers.py` - Тесты для IO handlers (PathResolver, ConfigLoader, ResourceLoader)
- `conftest.py` - Общие fixtures для всех тестов

## Запуск тестов

```bash
# Все тесты
pytest

# С подробным выводом
pytest -v

# Конкретный файл
pytest tests/test_models.py

# Конкретный тест
pytest tests/test_models.py::TestSlideConfig::test_create_valid_slide

# С покрытием
pytest --cov=. --cov-report=html
```

## Покрытие

Целевое покрытие: > 80%

Основные компоненты, которые должны быть покрыты:
- ✅ Модели данных (models/)
- ✅ IO handlers (io_handlers/)
- ⏳ Core логика (core/) - частично
- ⏳ CLI команды (cli/) - требуют интеграционных тестов

## Добавление новых тестов

1. Создайте файл `test_<module>.py`
2. Импортируйте `pytest`
3. Создайте классы `Test<ClassName>`
4. Напишите методы `test_<scenario>`
5. Используйте fixtures из `conftest.py`

Пример:

```python
import pytest
from my_module import my_function

class TestMyFunction:
    def test_basic_case(self):
        result = my_function(input_data)
        assert result == expected
    
    def test_error_case(self):
        with pytest.raises(ValueError):
            my_function(bad_input)
```
