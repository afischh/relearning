# quiet_logos agent (prepared)

Этот агент подготовлен так, чтобы:
- по умолчанию работать безопасно (stub)
- иметь точку подключения к облаку
- не ломать сайт до включения real-режима

## Режимы
- stub (по умолчанию)
- real (QUIET_LOGOS_MODE=real + OPENAI_API_KEY)

## Ручная проверка (stub)
python -m core.agents.quiet_logos.engine YYYY-MM-DD

Интеграция в сборку сайта выполняется отдельным шагом.
