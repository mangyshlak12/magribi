#!/usr/bin/env python3
from pathlib import Path
import secrets, os
root=Path(__file__).resolve().parent.parent
path=root/".env"
if path.exists():
    print(".env already exists; nothing overwritten")
else:
    password=secrets.token_urlsafe(32)
    content=f"""DJANGO_DEBUG=1
DJANGO_SECRET_KEY={secrets.token_urlsafe(64)}
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,api,backend
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
POSTGRES_USER=magribi
POSTGRES_PASSWORD={password}
POSTGRES_DB=magribi
DATABASE_URL=postgresql://magribi:{password}@127.0.0.1:5432/magribi
API_INTERNAL_URL=http://127.0.0.1:8000
"""
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w") as file:file.write(content)
    print("Created private local .env. Use different secrets for production.")
