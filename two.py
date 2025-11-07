import markdown
from bs4 import BeautifulSoup


def clean_markdown_for_notes(md_text: str) -> str:
    """
    Конвертирует Markdown в HTML, а затем извлекает
    только чистый текст, убивая все маркеры списков и форматирование.
    """
    if not md_text:
        return ""

    try:
        # 1. Конвертируем Markdown в HTML
        html = markdown.markdown(md_text)

        # 2. Используем BeautifulSoup, чтобы "раздеть" HTML до текста
        soup = BeautifulSoup(html, "html.parser")

        # 3. Извлекаем весь текст, BeautifulSoup умный и уберет теги
        text = soup.get_text(separator="\n").strip()

        # 4. Очистка от лишних пустых строк
        clean_text = "\n".join(
            line.strip() for line in text.splitlines() if line.strip()
        )

        return clean_text
    except Exception as e:
        print(f"Ошибка очистки Markdown: {e}")
        return md_text  # Возвращаем исходный текст в случае ошибки


if __name__ == "__main__":
    # Пример использования
    test_md = """
    Это *тест*.
    
    - Первый пункт
    - Второй пункт
    
    1. Нумерованный
    2. Второй нумерованный
    
    Код `print('hello')`
    """

    cleaned = clean_markdown_for_notes(test_md)
    print("--- ИСХОДНЫЙ ---")
    print(test_md)
    print("\n--- ОЧИЩЕННЫЙ ---")
    print(cleaned)
