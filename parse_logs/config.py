import os
from enum import Enum

CURRENT_DIR = os.path.dirname(__file__)
LOG_DIR = f"{os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))}/logs"


class Config(Enum):
    DAILY_AMOUNT = 45
    BLOCK_SIZE = 4
    BLOCK_DELIMITER = "---"
    LOG_FILE = f"{LOG_DIR}/cronjob.log"
    PURCHASE_TAG = "XBTGBP"  # asset/currency tag
    INVALID_KEY_ERROR = "Invalid key"
    INSUFFICIENT_FUNDS_ERROR = "Insufficient funds"
