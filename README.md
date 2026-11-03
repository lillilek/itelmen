# Ительменский словарь и корпус

Статический сайт с поиском по словарю, интерлинеарным корпусом и списком глосс. Готовая версия находится в `docs/`. Для GitHub Pages выберите Settings → Pages → Deploy from a branch → main → /docs → Save.

Для локального просмотра запустите `python -m http.server --directory docs 8766` и откройте http://localhost:8766/. Пояснения к глоссам редактируются в `docs/data/glossary.csv`.

Для пересборки положите экспортированные XML в `.private/texts/`, а редакционный CSV словаря в `.private/dictionary-source.csv`. Из корня репозитория выполните `python tools/build_site.py --output docs`. Существующие пояснения сохраняются при пересборке. Исходные материалы FieldWorks хранятся локально.
