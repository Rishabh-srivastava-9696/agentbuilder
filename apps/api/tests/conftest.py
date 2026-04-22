import os


# Keep test imports from failing on required production secrets.
os.environ.setdefault("SECRET_KEY", "test-secret-key")
