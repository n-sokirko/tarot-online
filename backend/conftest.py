"""pytest configuration for the backend."""


def pytest_configure():
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
