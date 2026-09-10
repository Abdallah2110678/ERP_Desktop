from pathlib import Path
import datetime

PHARMACY_NAME    = "مكتب عباد الرحمان"
PHARMACY_SUBTITLE = "صيدلية بيطرية متخصصة"
APP_VERSION      = "1.0"
APP_YEAR         = datetime.date.today().year
DB_PATH          = Path(__file__).parent / "pharmacy.db"
