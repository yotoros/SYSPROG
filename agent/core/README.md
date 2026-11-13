# Ядро агента

| Файл | Описание |
|------|----------|
| core.h | структура и объявление функции, шаг 5 |
| core_info.c | функция core_get_info, шаг 6 |
| show_info.c | программа проверки, шаг 7 |

## Сборка библиотеки

```cmd
cd agent/core
cl /nologo /W4 /LD core_info.c /Fe:sentry_core.dll
