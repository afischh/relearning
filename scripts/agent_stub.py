"""
quiet_agent — минимальный агент-комментатор.

Он не умный.
Он внимательный.
"""

from datetime import date

RULES = [
    "Отвечай коротко.",
    "Не объясняй, если не просят.",
    "Смотри на тон, а не на факты.",
    "Если текст тихий — будь тише.",
]

def comment(text: str) -> str:
    if not text.strip():
        return "…"

    if "тиш" in text.lower():
        return "Тишина — это тоже форма ответа."

    return "Я рядом. Продолжай."

if __name__ == "__main__":
    sample = "Сегодня было тихо."
    print(f"[{date.today()}] agent:", comment(sample))
