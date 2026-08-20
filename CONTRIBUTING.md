# Contributing

Use small, reviewable pull requests. Every behavior change needs a test, and every provider change must state its coverage and credential assumptions.

Before opening a pull request:

```powershell
python -m pip install -e ".[dev]"
ruff check tweetharbor
pytest -q
```

Do not commit `.env`, databases, cookies, bearer tokens, or captured production responses containing user data.
