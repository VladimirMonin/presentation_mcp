# Руководство по использованию Presentation Builder

## Оглавление

- [Быстрый старт](#быстрый-старт)
- [Конфигурационный файл](#конфигурационный-файл)
- [CLI команды](#cli-команды)
- [Макеты (Layouts)](#макеты-layouts)
- [Пути к файлам](#пути-к-файлам)
- [Markdown заметки](#markdown-заметки)
- [Расширяемость](#расширяемость)

---

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Подготовка файлов

Вам понадобятся:

- **Шаблон PowerPoint** (`template.pptx`) с нужными макетами
- **Конфигурационный JSON** файл с описанием слайдов
- **Изображения** для слайдов
- **Markdown файлы** для заметок (опционально)

### 3. Создание конфигурации

Создайте JSON файл (например, `config.json`):

```json
{
  "template_path": "template.pptx",
  "layout_name": "single_wide",
  "output_path": "result.pptx",
  "slides": [
    {
      "title": "Мой первый слайд",
      "slide_number": "1",
      "notes_source": "notes.md",
      "images": ["photo.jpg"]
    }
  ]
}
```

### 4. Генерация презентации

```bash
python main.py generate --config config.json
```

Готово! Презентация сохранена в `result.pptx`.

---

## Конфигурационный файл

### Структура JSON

```json
{
  "template_path": "<путь к шаблону PPTX>",
  "layout_name": "<имя макета из template>",
  "output_path": "<путь к выходному файлу>",
  "slides": [
    {
      "title": "<заголовок слайда>",
      "slide_number": "<номер слайда>",
      "notes_source": "<путь к MD файлу или inline текст>",
      "images": ["<путь к изображению 1>", "<путь к изображению 2>"]
    }
  ]
}
```

### Обязательные поля

- `template_path` — путь к шаблону PowerPoint
- `layout_name` — имя макета (должен существовать в шаблоне)
- `slides` — массив слайдов

### Опциональные поля

- `output_path` — если не указан, будет `output.pptx`
- `title` — заголовок слайда (по умолчанию пусто)
- `slide_number` — номер слайда (по умолчанию пусто)
- `notes_source` — заметки из MD файла или inline (по умолчанию пусто)
- `images` — массив путей к изображениям (по умолчанию пусто)

### Примеры

См. файлы в `doc/samples/`:

- `simple_example.json` — базовый пример с одним изображением
- `multi_image_example.json` — пример с двумя изображениями
- `absolute_paths_example.json` — пример с абсолютными путями

---

## CLI команды

### generate — Генерация презентации

```bash
python main.py generate --config <путь к JSON> [--output <файл>] [--verbose]
```

**Параметры:**

- `--config` — путь к JSON конфигурации (обязательный)
- `--output` — путь к выходному файлу (переопределяет значение из JSON)
- `--verbose` — подробный вывод процесса сборки

**Примеры:**

```bash
# Базовая генерация
python main.py generate --config slides.json

# С явным указанием выходного файла
python main.py generate --config slides.json --output presentation.pptx

# С подробным логированием
python main.py generate --config slides.json --verbose
```

### analyze — Анализ шаблона

```bash
python main.py analyze --template <путь к PPTX> [--layout <имя>]
```

**Параметры:**

- `--template` — путь к шаблону PowerPoint (обязательный)
- `--layout` — имя конкретного макета для детального анализа (опционально)

**Примеры:**

```bash
# Список всех макетов в шаблоне
python main.py analyze --template template.pptx

# Детальный анализ конкретного макета
python main.py analyze --template template.pptx --layout "Blank"
```

### help — Справка

```bash
python main.py help
```

Выводит справку по всем доступным командам и их использованию.

---

## Макеты (Layouts)

### Встроенные макеты

Система поставляется с 4 предустановленными макетами:

#### 1. `single_wide` — Одно широкое изображение

- **1 изображение**: горизонтальное размещение (16:9 оптимально)
- Использование: пейзажи, панорамы, широкие диаграммы

#### 2. `single_tall` — Одно высокое изображение

- **1 изображение**: вертикальное размещение (9:16 оптимально)
- Использование: портреты, скриншоты мобильных приложений

#### 3. `two_stack` — Два изображения вертикально

- **2 изображения**: расположены друг над другом
- Использование: сравнение "до/после", этапы процесса

#### 4. `two_tall_row` — Два высоких изображения рядом

- **2 изображения**: два вертикальных изображения в ряд
- Использование: сравнение портретов, скриншоты

### Создание собственных макетов

См. раздел [Расширяемость](#расширяемость).

---

## Пути к файлам

### Относительные пути

По умолчанию все пути в JSON интерпретируются **относительно расположения JSON файла**.

**Пример:**

Структура файлов:

```
project/
  config/
    slides.json          ← JSON файл здесь
  images/
    photo.jpg
  notes/
    slide1.md
  template.pptx
```

Содержимое `slides.json`:

```json
{
  "template_path": "../template.pptx",
  "slides": [
    {
      "notes_source": "../notes/slide1.md",
      "images": ["../images/photo.jpg"]
    }
  ]
}
```

При запуске `python main.py generate --config config/slides.json` все пути будут правильно разрешены относительно `config/`.

### Абсолютные пути

Можно использовать абсолютные пути:

```json
{
  "template_path": "C:/Templates/template.pptx",
  "slides": [
    {
      "notes_source": "C:/Notes/slide1.md",
      "images": ["C:/Images/photo.jpg"]
    }
  ]
}
```

### Смешивание путей

Можно комбинировать абсолютные и относительные пути в одном файле:

```json
{
  "template_path": "C:/Templates/corporate.pptx",
  "slides": [
    {
      "notes_source": "notes/slide1.md",
      "images": ["../shared/logo.png"]
    }
  ]
}
```

---

## Markdown заметки

### Поддержка Markdown

Система автоматически конвертирует Markdown в plain text для заметок PowerPoint.

**Поддерживаемые элементы:**

- Заголовки (`#`, `##`, etc.)
- Жирный текст (`**текст**`)
- Курсив (`*текст*`)
- Списки (нумерованные и маркированные)
- Ссылки
- Цитаты
- Код-блоки
- Таблицы

### Inline текст vs файлы

**Вариант 1: Markdown файл**

```json
{
  "notes_source": "notes/slide1.md"
}
```

**Вариант 2: Inline текст**

```json
{
  "notes_source": "Это обычный текст заметки"
}
```

Система автоматически определяет, является ли `notes_source` путем к файлу или inline текстом:

- Если файл существует → загружается содержимое
- Если файла нет → используется как inline текст

### Примеры Markdown файлов

См. `doc/samples/notes1.md` и `doc/samples/notes2.md`.

### Legacy поддержка

Старые конфигурации с полем `notes_text` автоматически мигрируются:

```json
// Старый формат (работает)
{
  "notes_text": "Заметка"
}

// Новый формат (рекомендуется)
{
  "notes_source": "Заметка"
}
```

---

## Расширяемость

### Добавление новых макетов

Макеты регистрируются в `config/settings.py`.

**Шаг 1:** Создайте `LayoutBlueprint`:

```python
from models.layout_registry import LayoutBlueprint, ImagePlacement
from pptx.util import Inches

my_custom_layout = LayoutBlueprint(
    name="my_custom",
    placeholders={
        "TITLE": 0,
        "NUMBER": 1,
        "IMAGE_1": 10,
        "IMAGE_2": 11
    },
    image_placements=[
        ImagePlacement(
            placeholder_idx=10,
            left=Inches(1),
            top=Inches(2),
            width=Inches(4),
            height=Inches(3)
        ),
        ImagePlacement(
            placeholder_idx=11,
            left=Inches(6),
            top=Inches(2),
            width=Inches(4),
            height=Inches(3)
        )
    ]
)
```

**Шаг 2:** Зарегистрируйте макет:

```python
from config.settings import register_default_layouts
from models.layout_registry import get_layout_registry

# После регистрации дефолтных макетов
register_default_layouts()

# Добавьте свой
registry = get_layout_registry()
registry.register(my_custom_layout)
```

**Шаг 3:** Используйте в JSON:

```json
{
  "layout_name": "my_custom",
  ...
}
```

### Анализ шаблона для новых макетов

Используйте команду `analyze` для изучения структуры вашего шаблона:

```bash
python main.py analyze --template template.pptx --layout "Your Layout Name"
```

Это покажет:

- Индексы placeholder'ов
- Типы placeholder'ов (TITLE, PICTURE, etc.)
- Координаты и размеры

Используйте эту информацию для создания `LayoutBlueprint`.

---

## Миграция со старых версий

### Миграция one.py, two.py, three.py

Старые скрипты находятся в архиве (`archive/` после очистки).

**Изменения:**

1. **Вместо прямого запуска Python скриптов** → CLI команды

   ```bash
   # Было
   python three.py config.json
   
   # Стало
   python main.py generate --config config.json
   ```

2. **Поле `notes_text`** → `notes_source`

   ```json
   // Было
   {"notes_text": "Текст"}
   
   // Стало (backward compatible)
   {"notes_source": "Текст"}
   ```

3. **Inline текст vs MD файлы**
   - Старая версия: только inline текст
   - Новая версия: поддержка MD файлов + inline текст

### Автоматическая миграция

Система автоматически мигрирует `notes_text` → `notes_source` при загрузке старых конфигов.

---

## Troubleshooting

### Ошибка: "Layout not found"

**Проблема:** Указанный макет не найден в шаблоне.

**Решение:**

1. Проверьте список доступных макетов:

   ```bash
   python main.py analyze --template template.pptx
   ```

2. Убедитесь, что имя макета указано правильно (case-sensitive)
3. Проверьте, что макет зарегистрирован в `config/settings.py`

### Ошибка: "Image not found"

**Проблема:** Изображение не найдено по указанному пути.

**Решение:**

1. Проверьте, что путь указан правильно
2. Если используете относительные пути, убедитесь, что они указаны относительно JSON файла
3. Используйте `--verbose` для подробной диагностики:

   ```bash
   python main.py generate --config config.json --verbose
   ```

### Ошибка: "Mismatch between images and placements"

**Проблема:** Количество изображений не соответствует количеству размещений в макете.

**Поведение:**

- Если изображений **больше** → лишние игнорируются (предупреждение)
- Если изображений **меньше** → некоторые placeholder'ы останутся пустыми (предупреждение)

**Решение:**

1. Проверьте количество изображений в слайде
2. Убедитесь, что используете правильный макет:
   - `single_wide` / `single_tall` → 1 изображение
   - `two_stack` / `two_tall_row` → 2 изображения

---

## Дополнительные ресурсы

- **План рефакторинга:** `doc/plan/refactor_plan.md`
- **Полный pipeline:** `doc/full_pipeline.md`
- **Тесты:** `tests/README.md`
- **Примеры конфигураций:** `doc/samples/`

---

## Поддержка

При возникновении проблем:

1. Проверьте логи с флагом `--verbose`
2. Убедитесь, что все зависимости установлены
3. Проверьте формат JSON конфигурации
4. Изучите примеры в `doc/samples/`
