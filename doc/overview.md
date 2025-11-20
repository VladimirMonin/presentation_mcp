# Presentation Builder — Автоматизация создания PowerPoint презентаций

## Назначение

Presentation Builder — это система автоматической генерации PowerPoint презентаций из JSON-конфигурации.
Создавайте слайды с изображениями и заметками докладчика автоматически.

## Основные возможности

- ✅ Создание слайдов из JSON-конфигурации
- ✅ Поддержка разных типов слайдов (обычные + титульные YouTube)
- ✅ Переопределение макета PowerPoint на уровне слайда
- ✅ Умное масштабирование изображений с сохранением пропорций
- ✅ 6 готовых макетов размещения изображений
- ✅ Поддержка заметок докладчика из Markdown
- ✅ Автоматическая конвертация WebP в PNG
- ✅ **НОВОЕ!** Добавление аудио (озвучка, музыка) к слайдам

---

## Доступные макеты PowerPoint (layout_name)

В шаблоне `youtube_base.pptx` доступны следующие макеты:

### `TitleLayout` — Титульный слайд

Используется для обложки презентации или YouTube видео.

**Обязательные поля:**

- `slide_type: "title_youtube"`
- `layout_type: "title_youtube"`
- `layout_name: "TitleLayout"`
- `title` — название канала/презентации
- `subtitle` — описание серии (обязательно!)
- `images` — ровно 1 изображение (квадратное, для логотипа)

### `VideoLayout` — Контентный слайд

Используется для обычных слайдов с контентом.

**Обязательные поля:**

- `slide_type: "content"`
- `layout_type` — один из: `single_wide`, `single_tall`, `two_stack`, `two_tall_row`, `three_stack`
- `title` — заголовок слайда
- `images` — от 1 до 3 изображений (в зависимости от layout_type)

---

## Доступные макеты размещения изображений (layout_type)

1. **single_wide** — одно широкое изображение (16:9)
2. **single_tall** — одно высокое изображение (9:16)
3. **two_stack** — два изображения друг под другом
4. **two_tall_row** — два высоких изображения рядом
5. **three_stack** — три изображения вертикально
6. **title_youtube** — титульный слайд YouTube (логотип канала)

---

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Создание конфигурации

```json
{
  "template_path": "templates/youtube_base.pptx",
  "layout_name": "VideoLayout",
  "output_path": "output.pptx",
  "slides": [
    {
      "slide_type": "title_youtube",
      "layout_type": "title_youtube",
      "layout_name": "TitleLayout",
      "title": "Мой YouTube Канал",
      "subtitle": "Python для начинающих",
      "images": ["logo.png"]
    },
    {
      "slide_type": "content",
      "layout_type": "single_wide",
      "title": "Заголовок слайда",
      "notes_source": "Текст заметок докладчика",
      "images": ["path/to/image.png"]
    }
  ]
}
```

### 3. Генерация презентации

```bash
python main.py generate config.json
```

## Доступные команды CLI

### `generate` — генерация презентации

```bash
python main.py generate slides.json
python main.py generate slides.json -o output.pptx
python main.py generate slides.json -t custom_template.pptx
```

### `analyze` — анализ структуры шаблона

```bash
python main.py analyze template.pptx
python main.py analyze template.pptx -l CustomLayout
python main.py analyze template.pptx --list
```

### `help` — справка

```bash
python main.py help
```

## Доступные макеты

Система включает 6 предустановленных макетов размещения изображений:

1. **single_wide** — одно широкое изображение (16:9)
2. **single_tall** — одно высокое изображение (9:16)
1. **single_wide** — одно широкое изображение (16:9)
2. **single_tall** — одно высокое изображение (9:16)
3. **two_stack** — два изображения друг под другом
4. **two_tall_row** — два высоких изображения рядом
5. **three_stack** — три изображения вертикально
6. **title_youtube** — титульный слайд YouTube (логотип канала)

Подробное описание каждого макета см. в `doc/layouts/<имя_макета>.md`.

## MCP Server

Проект включает MCP-сервер для интеграции с AI-агентами (Claude, ChatGPT и др.).

### Доступные MCP-инструменты

- `create_presentation` — создание презентации из JSON
- `get_layout_documentation` — получение документации по макетам

### Запуск MCP-сервера

```bash
python mcp_server.py
```

## Структура JSON-конфигурации

### Корневой объект

| Поле | Тип | Описание |
|------|-----|----------|
| `template_path` | string | Путь к файлу шаблона PPTX |
| `layout_name` | string | Имя макета в шаблоне (по умолчанию: VideoLayout) |
| `output_path` | string | Путь к выходному файлу |
| `slides` | array | Массив объектов слайдов |

### Объект слайда

| Поле | Тип | Описание |
|------|-----|----------|
| `slide_type` | string | Тип слайда: `content` (по умолчанию) или `title_youtube` |
| `layout_type` | string | Тип макета размещения изображений (см. выше список) |
| `layout_name` | string | Переопределение макета PowerPoint для конкретного слайда (TitleLayout или VideoLayout) |
| `title` | string | Заголовок слайда |
| `notes_source` | string | Текст заметок или путь к .md файлу |
| `images` | array | Массив путей к изображениям |

**Дополнительные поля для `slide_type: "title_youtube"`:**

| Поле | Тип | Описание |
|------|-----|----------|
| `subtitle` | string | Подзаголовок/описание серии (обязательно) |
| `series_number` | string | Номер части серии (опционально) |

## Умное масштабирование

Система автоматически вычисляет размеры изображений с сохранением пропорций:

- Если изображение **шире** отведённой области → фиксируется ширина
- Если изображение **выше** отведённой области → фиксируется высота
- Изображение **никогда не растягивается** и не искажается

## Поддерживаемые форматы изображений

- ✅ PNG, JPEG, BMP, GIF, TIFF
- ✅ WebP (автоматическая конвертация в PNG)

---

**Дата обновления:** 19 ноября 2025  
**Версия:** 2.0
