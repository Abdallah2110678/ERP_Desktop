import sys
from pathlib import Path
import datetime


def _app_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


PHARMACY_NAME    = "مكتب عباد الرحمان"
PHARMACY_SUBTITLE = "صيدلية بيطرية متخصصة"
APP_VERSION      = "1.0"
APP_YEAR         = datetime.date.today().year
DB_PATH          = _app_dir() / "pharmacy.db"
