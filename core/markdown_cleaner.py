"""
Очистка Markdown текста для заметок докладчика.

Этот модуль преобразует Markdown разметку в чистый читаемый текст,
удаляя все элементы форматирования, но сохраняя структуру и читаемость.
"""

import markdown
from bs4 import BeautifulSoup
from typing import Optional


def clean_markdown_for_notes(md_text: str) -> str:
    """
    Конвертирует Markdown в чистый текст для заметок докладчика.

    Процесс:
    1. Markdown → HTML (через библиотеку markdown)
    2. HTML → plain text (через BeautifulSoup)
    3. Очистка от лишних пустых строк
    4. Нормализация пробелов

    Args:
        md_text: Текст в формате Markdown.

    Returns:
        Чистый текст без форматирования, готовый для заметок.

    Note:
        - Списки превращаются в строки без маркеров
        - Жирный/курсив удаляются
        - Ссылки превращаются в текст
        - Заголовки становятся обычным текстом
        - Код-блоки сохраняются как текст

    Example:
        >>> md = "# Заголовок\\n\\n- Пункт **жирный**\\n- Другой"
        >>> clean = clean_markdown_for_notes(md)
        >>> print(clean)
        Заголовок
        Пункт жирный
        Другой
    """
    if not md_text:
        return ""

    try:
        # Шаг 1: Конвертируем Markdown в HTML
        html = markdown.markdown(md_text)

        # Шаг 2: Парсим HTML с BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Шаг 3: Извлекаем текст (BeautifulSoup автоматически убирает теги)
        # separator="\n" сохраняет структуру абзацев
        text = soup.get_text(separator="\n").strip()

        # Шаг 4: Очистка от множественных пустых строк
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        return clean_text

    except Exception as e:
        # В случае ошибки возвращаем исходный текст
        # (лучше показать что-то, чем ничего)
        print(f"⚠ Ошибка очистки Markdown: {e}")
        return md_text


def clean_markdown_preserve_structure(md_text: str) -> str:
    """
    Очищает Markdown с сохранением структуры абзацев и отступов.

    В отличие от clean_markdown_for_notes, эта функция сохраняет
    пустые строки между абзацами для лучшей читаемости.

    Args:
        md_text: Текст в формате Markdown.

    Returns:
        Чистый текст с сохранением структуры параграфов.

    Example:
        >>> md = "Первый параграф.\\n\\nВторой параграф."
        >>> clean = clean_markdown_preserve_structure(md)
        >>> print(clean)
        Первый параграф.

        Второй параграф.
    """
    if not md_text:
        return ""

    try:
        html = markdown.markdown(md_text)
        soup = BeautifulSoup(html, "html.parser")

        # Обрабатываем каждый блочный элемент отдельно
        blocks = []
        for element in soup.find_all(
            ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"]
        ):
            text = element.get_text().strip()
            if text:
                blocks.append(text)

        # Соединяем блоки двойным переводом строки
        return "\n\n".join(blocks)

    except Exception as e:
        print(f"⚠ Ошибка очистки Markdown: {e}")
        return md_text


def validate_markdown(md_text: str) -> Optional[str]:
    """
    Проверяет корректность Markdown текста.

    Args:
        md_text: Текст для валидации.

    Returns:
        None, если текст валиден.
        Строка с описанием ошибки, если найдена проблема.

    Example:
        >>> error = validate_markdown("# Заголовок\\n\\nТекст")
        >>> if error:
        ...     print(f"Ошибка: {error}")
    """
    if not md_text:
        return "Пустой текст"

    try:
        # Пытаемся преобразовать
        html = markdown.markdown(md_text)

        # Базовая проверка результата
        if not html or html.isspace():
            return "Markdown преобразовался в пустой HTML"

        return None  # Всё ОК

    except Exception as e:
        return f"Ошибка парсинга: {str(e)}"


# Тестовые кейсы (для документации и проверки)

TEST_CASES = [
    {
        "name": "Простой текст",
        "input": "Просто текст без разметки.",
        "expected": "Просто текст без разметки.",
    },
    {
        "name": "Жирный и курсив",
        "input": "Текст с **жирным** и *курсивом*.",
        "expected": "Текст с жирным и курсивом.",
    },
    {
        "name": "Заголовки",
        "input": "# Заголовок 1\n## Заголовок 2\nТекст",
        "expected": "Заголовок 1\nЗаголовок 2\nТекст",
    },
    {
        "name": "Списки",
        "input": "- Первый пункт\n- Второй пункт\n- Третий пункт",
        "expected": "Первый пункт\nВторой пункт\nТретий пункт",
    },
    {
        "name": "Нумерованные списки",
        "input": "1. Один\n2. Два\n3. Три",
        "expected": "Один\nДва\nТри",
    },
    {
        "name": "Ссылки",
        "input": "Посмотрите [эту ссылку](https://example.com).",
        "expected": "Посмотрите эту ссылку.",
    },
    {
        "name": "Код inline",
        "input": "Используйте `код` в тексте.",
        "expected": "Используйте код в тексте.",
    },
    {
        "name": "Блок кода",
        "input": "```python\nprint('hello')\n```",
        "expected": "print('hello')",
    },
    {"name": "Пустой текст", "input": "", "expected": ""},
    {
        "name": "Множественные пустые строки",
        "input": "Первая строка\n\n\n\nВторая строка",
        "expected": "Первая строка\nВторая строка",
    },
]


def run_tests() -> bool:
    """
    Запускает тестовые кейсы для проверки работы функции.

    Returns:
        True, если все тесты прошли успешно, иначе False.
    """
    print("=" * 60)
    print("ТЕСТЫ: Очистка Markdown")
    print("=" * 60)

    passed = 0
    failed = 0

    for test in TEST_CASES:
        result = clean_markdown_for_notes(test["input"])

        if result == test["expected"]:
            passed += 1
            print(f"✓ {test['name']}")
        else:
            failed += 1
            print(f"✗ {test['name']}")
            print(f"  Ожидалось: {repr(test['expected'])}")
            print(f"  Получено:  {repr(result)}")

    print()
    print(f"Пройдено: {passed}/{len(TEST_CASES)}")
    print(f"Провалено: {failed}/{len(TEST_CASES)}")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    # Запуск тестов при прямом вызове модуля
    success = run_tests()
    exit(0 if success else 1)
