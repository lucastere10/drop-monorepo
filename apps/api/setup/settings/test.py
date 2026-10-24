import tempfile
from pathlib import Path

from .base import *

LOCAL_STORAGE_ROOT = Path(tempfile.mkdtemp(prefix="drop-test-uploads-"))

DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND_KIND = "console"
QUEUE_BACKEND = "inline"
STORAGE_BACKEND = "local"
