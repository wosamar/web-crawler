from enum import Enum
from pathlib import Path


class AreaName(str, Enum):  # API選擇地區
    taipei = "台北市"
    new_taipei = "新北市"

BASEDIR = Path(__file__).resolve().parent