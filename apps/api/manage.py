#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main() -> None:
    from dotenv import load_dotenv

    api_dir = Path(__file__).resolve().parent
    repo_root = api_dir.parents[1]
    load_dotenv(repo_root / ".env")
    load_dotenv(api_dir / ".env")

    from setup.env_contract import django_settings_module

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", django_settings_module())
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
