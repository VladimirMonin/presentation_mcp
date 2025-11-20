# Архитектура Presentation Builder v2.0

## Композиционная архитектура (Composition over Inheritance)

С версии 2.0 система следует принципу **Composition over Inheritance** для размещения контента на слайдах.

## Компоненты системы

### 1. PresentationBuilder (Оркестратор)

**Ответственность:**

- Загрузка шаблона PPTX
- Создание слайдов согласно конфигурации
- Заполнение текстовых полей (заголовок, номер, заметки)
- **Делегирование** размещения контента специализированным классам

**Размер:** ~287 строк (сокращено с 516 на 44% после рефакторинга)

**Файл:** `core/presentation_builder.py`

### 2. ImagePlacer (Специалист по изображениям)

**Ответственность:**

- Резолвинг путей через `ResourceLoader`
- Автоматическая конвертация WebP → PNG (in-memory)
- Умное масштабирование согласно макету
- Размещение на слайде через `add_picture`

**Файл:** `core/placers/image_placer.py`

### 3. MediaPlacer (Специалист по аудио/видео)

**Ответственность:**

- Резолвинг путей через `ResourceLoader`
- Вставка аудио/видео (workaround через `add_movie`)
- XML-модификация для автоматического воспроизведения

**Файл:** `core/placers/media_placer.py`

## Принципы SOLID

### Single Responsibility Principle (SRP)

Каждый класс имеет одну ответственность:

- `PresentationBuilder` — оркестрация
- `ImagePlacer` — работа с изображениями
- `MediaPlacer` — работа с медиа

### Open/Closed Principle (OCP)

Добавление нового типа контента **не требует изменения** `PresentationBuilder`:

```python
# Добавление поддержки таблиц:
class TablePlacer:
    def place_tables(self, slide, table_data, layout_config):
        # Логика размещения таблиц
        pass

# В PresentationBuilder просто добавляем делегирование:
if slide_config.get("tables"):
    self.table_placer.place_tables(slide, slide_config["tables"], layout_config)
```

### Dependency Inversion Principle (DIP)

Все компоненты зависят от абстракций (`ResourceLoader`, `LayoutRegistry`), а не от конкретных реализаций.

## Паттерн использования

```python
from models import LayoutRegistry
from io_handlers import ResourceLoader, PathResolver
from core import PresentationBuilder
from config import register_default_layouts

# Настройка зависимостей
resolver = PathResolver(Path("config.json"))
loader = ResourceLoader(resolver)
registry = LayoutRegistry()
register_default_layouts(registry)

# Создание билдера (автоматически создаёт ImagePlacer и MediaPlacer)
builder = PresentationBuilder(registry, loader)

# Сборка презентации
prs = builder.build(config, Path("template.pptx"))
builder.save(prs, Path("output.pptx"))
```

## Будущие расширения

Архитектура готова для добавления новых типов контента без изменения существующего кода:

- **TextPlacer** — размещение текстовых блоков из Markdown
- **TablePlacer** — вставка таблиц из CSV/JSON
- **ChartPlacer** — генерация графиков из данных
- **VideoPlacer** — расширенная работа с видео (отдельно от MediaPlacer)

## Преимущества новой архитектуры

1. **Изолированное тестирование** — каждый placer тестируется отдельно
2. **Легкость отладки** — ошибка в работе с изображениями изолирована в ImagePlacer
3. **Независимое развитие** — можно улучшать MediaPlacer не трогая ImagePlacer
4. **Переиспользование** — placers можно использовать в других проектах

## Логирование

Каждый placer логирует свои операции согласно `technical/logging.md`:

- Собирает ошибки в списки
- Передаёт их обратно в билдер
- Билдер агрегирует ошибки со всех placers

## Диаграмма компонентов

```
PresentationBuilder (Orchestrator)
    ├── ImagePlacer (Images)
    │   ├── ResourceLoader (Path Resolution)
    │   ├── ImageProcessor (WebP Conversion)
    │   └── LayoutRegistry (Layout Metadata)
    │
    └── MediaPlacer (Audio/Video)
        ├── ResourceLoader (Path Resolution)
        └── OOXML Manipulation (Autoplay)
```
