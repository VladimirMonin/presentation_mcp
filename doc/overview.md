# Presentation Builder — Автоматизация создания PowerPoint презентаций

> ⚠️ **ВАЖНО**: Эта документация является единым источником правды как для людей, так и для AI-агентов через MCP (Model Context Protocol).
> При обновлении функционала обновляйте соответствующие файлы в `doc/`.

## Назначение

Presentation Builder — это система автоматической генерации PowerPoint презентаций из JSON-конфигурации.
Проект предназначен для быстрого создания слайдов с изображениями и заметками докладчика.

## Основные возможности

- ✅ Создание слайдов из JSON-конфигурации
- ✅ **Полиморфная система типов слайдов** (content, title_youtube)
- ✅ Умное масштабирование изображений с сохранением пропорций
- ✅ 6 готовых макетов размещения изображений
- ✅ Поддержка заметок докладчика из Markdown
- ✅ Автоматическая конвертация WebP в PNG
- ✅ MCP-сервер для интеграции с AI-агентами

## Архитектура проекта

```
presentation_mcp/
├── cli/              # CLI команды (generate, analyze, help)
├── config/           # Настройки и регистрация макетов
├── core/             # Ядро системы (builder, image processor)
├── io_handlers/      # Загрузка конфигов, путей, ресурсов
├── models/           # Модели данных (config_schema, layout_registry)
├── doc/              # Документация (ЭТОТ ФАЙЛ)
│   ├── layouts/      # Описание макетов
│   └── samples/      # Примеры конфигураций
├── main.py           # CLI точка входа
├── mcp_server.py     # MCP-сервер для AI-агентов
└── template.pptx     # Шаблон презентации
```

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Создание конфигурации

```json
{
  "template_path": "template.pptx",
  "layout_name": "VideoLayout",
  "output_path": "output.pptx",
  "slides": [
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
| `layout_type` | string | Тип макета (single_wide, two_stack, title_youtube и т.д.) |
| `title` | string | Заголовок слайда |
| `notes_source` | string | Текст заметок или путь к .md файлу |
| `images` | array | Массив путей к изображениям |

**Дополнительные поля для `slide_type: "title_youtube"`:**

| Поле | Тип | Описание |
|------|-----|----------|
| `subtitle` | string | Подзаголовок/описание серии |
| `series_number` | string | Номер части серии (опционально) |

## Умное масштабирование

Система автоматически вычисляет размеры изображений с сохранением пропорций:

- Если изображение **шире** отведённой области → фиксируется ширина
- Если изображение **выше** отведённой области → фиксируется высота
- Изображение **никогда не растягивается** и не искажается

## Поддерживаемые форматы изображений

- ✅ PNG, JPEG, BMP, GIF, TIFF (нативная поддержка python-pptx)
- ✅ WebP (автоматическая конвертация в PNG)

## Расширение системы

### Добавление нового макета

1. Откройте `config/settings.py`
2. Создайте новый `LayoutBlueprint` с координатами
3. Зарегистрируйте через `registry.register()`
4. Создайте документацию в `doc/layouts/<имя>.md`

### Добавление нового шаблона PPTX

1. Проанализируйте индексы placeholder: `python main.py analyze new_template.pptx`
2. Обновите константы `PLACEHOLDER_TITLE_IDX` и `PLACEHOLDER_SLIDE_NUM_IDX` в `config/settings.py`
3. Укажите новый `template_path` в JSON-конфигурации

## Лицензия и авторство

Разработано для автоматизации создания учебных презентаций.
GitHub Copilot | 2025
