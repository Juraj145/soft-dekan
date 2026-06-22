"""Vstupný bod aplikácie pre PyInstaller."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from volby_dekana.app import main  # noqa: E402

if __name__ == "__main__":
    main()
