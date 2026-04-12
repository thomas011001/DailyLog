---
trigger: always_on
---

Always prefix all Python and Django management commands with poetry run. Never execute commands like python manage.py; instead, use poetry run python manage.py to ensure all operations are performed within the project's virtual environment.