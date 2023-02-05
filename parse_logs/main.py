import argparse
import json
import math
import re
import sys
from contextlib import contextmanager
from datetime import datetime
from typing import Callable, Tuple

import pandas as pd
from config import Config

"""A block of logs is appended after each attempted purchase to the log file.
A block consists of 4 lines: a block delimiter, timestamp, API response data
and a reference to the amount of fiat spent and the corresponding amount of
crypto asset purchased."""


class ResponseError(Exception):
    pass


class NoLogsError(Exception):
    pass


@contextmanager
def surpress_exception_traceback():
    default = getattr(sys, "tracebacklimit", 1000)  # 1000 is Python's default
    sys.tracebacklimit = 0
    yield
    sys.tracebacklimit = default


class LogParser:
    daily_amount = Config.DAILY_AMOUNT.value
    block_size = Config.BLOCK_SIZE.value
    block_delimiter = Config.BLOCK_DELIMITER.value
    log_file = Config.LOG_FILE.value
    log_file_errors = [
        Config.INVALID_KEY_ERROR.value,
        Config.INSUFFICIENT_FUNDS_ERROR.value,
    ]
    PURCHASE_TAG = Config.PURCHASE_TAG.value

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.logs = self.get_logs()
        self.last_good_response = None
        self.last_buy_date = None
        self.has_error = False

    def __repr__(self) -> str:
        return (
            f"Last buy date: {self.last_buy_date} \n"
            f"Last good response: {self.last_good_response}"
        )

    def get_logs(self) -> list:
        with open(self.log_file, "r") as logs:
            lines = logs.readlines()[::-1]
        return lines

    def get_last_buy_date(self) -> datetime:
        self.last_good_response, line_number = self._get_last_good_response(start=0)
        block_begining = self._get_block_begining(start=line_number)
        self.last_buy_date = self._get_date(start=block_begining)

        if self.verbose:
            print(self)

        return self.last_buy_date

    def _iterate_block(
        self, start: int, func: Callable, *args, **kwargs
    ) -> Tuple[Callable, int]:
        """Iterates over a block of lines from a log file.
        Attempt to extract data from the log line or move to the next line on error
        or to the next block if there are errors in the response data."""
        for i in range(start, start + self.block_size):
            try:
                line = self._get_log_line(i)
                return func(line, *args, **kwargs), i
            except ValueError:
                continue
            except ResponseError:
                return self._iterate_block(start + self.block_size, func)
            except IndexError as err:
                with surpress_exception_traceback():
                    raise NoLogsError("Ran out of logs.") from err

    def _get_log_line(self, index) -> str:
        return self.logs[index].rstrip()

    def _get_last_good_response(self, start: int) -> Tuple[dict, int]:
        """Get the last error-free response."""
        return self._iterate_block(start, self._get_response)

    def check_stats(
        self, file_name: str = "stats.pkl", build_dataframe: bool = True
    ) -> None:
        """Prints some basic stats from the logs and builds a dataframe to
        be used for analysis."""
        purchases_in_crypto = []
        dates_purchased = []
        purchases_in_fiat = []

        for index, line in enumerate(self.logs):
            # log formatting has differed over time so we can't rely on block size
            buy_match = re.search(rf"buy \d\.\d+ {self.PURCHASE_TAG}", line)
            quantity_match = None

            if line.startswith("Quantity"):
                # This simply looks at the next line.
                has_error_in_block = json.loads(self.logs[index - 1])["error"]
                if not has_error_in_block:
                    quantity_match = re.search(r"\d+ \w+:", line)
                    fiat_amount, _ = quantity_match.group(0).split()
                    purchases_in_fiat.append(int(fiat_amount))

            if buy_match:
                _, amount, _ = buy_match.group(0).split()
                amount = float(amount)
                purchases_in_crypto.append(amount)

                block_begining = self._get_block_begining(index)
                date_purchased = self._get_date(block_begining)
                dates_purchased.append(date_purchased)

        if not len(purchases_in_crypto) == len(purchases_in_fiat):
            print("WARNING: Mismatch in crypto and fiat purchases.")

        print(
            f"Total purchase value in BTC: {sum(purchases_in_crypto)}\n",
            f"Total purchase value in fiat: {sum(purchases_in_fiat)} GBP \n",
            f"Num purchases: {len(purchases_in_crypto)}\n",
            f"Largest purchase: {max(purchases_in_crypto)} BTC "
            f"/ {max(purchases_in_fiat)} GBP \n",
            f"Smallest purchase: {min(purchases_in_crypto)}",
            f"/ {min(purchases_in_fiat)} GBP \n",
        )

        if build_dataframe:
            data = {
                "amount_crypto": purchases_in_crypto,
                "amount_fiat": purchases_in_fiat,
                "date": dates_purchased,
            }
            df = pd.DataFrame(data)
            df.to_pickle(f'parse_logs/{file_name}')

    def _get_response(self, line: str) -> dict:
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            raise ValueError
        else:
            if data["error"]:
                if not self.has_error:
                    self.has_error = True
                    self._send_error_email(data["error"])
                raise ResponseError
            return data

    def _get_block_begining(self, start: int) -> int:
        """Get first line number of the block from any line in the block."""
        for i in range(start, -1, -1):
            if not self._get_log_line(i).startswith(self.block_delimiter):
                continue
            return i

    def _get_amount_purchased(self, start: int) -> int:
        """Gets amount purchased given first line number in the block."""
        amount = self._iterate_block(start, self._get_quantity)
        return amount

    def _get_quantity(self, line: str) -> int:
        if line.startswith("Quantity"):
            match = re.search(r"\d+ \w+:", line)
            if match:
                amount, _ = match.group(0).split()
                return int(amount)
            import pdb

            pdb.set_trace()
        else:
            raise ValueError

    def _get_date(self, start: int) -> datetime:
        """Gets date of purchase given first line number in the block."""
        formatted_line, _ = self._iterate_block(start, self._get_date_format)
        return datetime.strptime(formatted_line, "%a %d %b %H:%M:%S %Y")

    def _get_date_format(self, line: str) -> str:
        date_match = re.search(r"\d{2}:\d{2}:\d{2} \w{3}", line)
        if date_match:
            date_elements = line.split()
            # Standardises the ordering of the date and time given that
            # it is always partially ordered.
            weekday = date_elements[0]
            day_num, month = sorted(date_elements[1:3])
            _, year, time = sorted(date_elements[3:], key=len)
            return " ".join([weekday, day_num, month, time, year])
        else:
            raise ValueError

    def get_days_since(self, date: datetime) -> int:
        time_diff = datetime.now() - date
        return math.floor(time_diff.total_seconds() / 60 / 60 / 24)

    def get_amount_to_buy(self, no_of_days: int) -> int:
        return self.daily_amount * no_of_days

    def _send_error_email(self, error_msg: str) -> None:
        for log_file_error in self.log_file_errors:
            if log_file_error in error_msg:
                send_email(log_file_error)


def send_email(message: str):
    pass


def main():
    args = parse_args(sys.argv[1:])
    parse_logs = LogParser(verbose=args.verbose)

    if args.get_days or args.get_amount:
        last_buy_date = parse_logs.get_last_buy_date()
        days_to_buy = parse_logs.get_days_since(last_buy_date)
        if args.get_days:
            print(f"Days to buy: {days_to_buy}") if args.verbose else print(days_to_buy)

    if args.get_amount:
        amount_to_buy = parse_logs.get_amount_to_buy(days_to_buy)
        print(f"amount to buy: £{amount_to_buy}") if args.verbose else print(
            amount_to_buy
        )

    if args.stats:
        parse_logs.check_stats(file_name=args.file_name, build_dataframe=args.build)


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stats",
        default=False,
        action="store_true",
        help="Get some stats from the logs.",
    )
    parser.add_argument(
        "--build",
        default=True,
        action="store_true",
        help="Builds a new dataframe and save to .pkl file for use in analysis.ipnyb.",
    )
    parser.add_argument(
        "-file-name",
        default="stats.pkl",
        help="File name of the pickled dataframe.",
    )
    parser.add_argument(
        "--get-days",
        default=False,
        action="store_true",
        help="Gets the number of days to buy.",
    )
    parser.add_argument(
        "--get-amount",
        default=False,
        action="store_true",
        help="Get amount to purchase (Number of days * amount).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        default=False,
        action="store_true",
        help="Run in verbose mode.",
    )
    return parser.parse_args(args)


if __name__ == "__main__":
    main()
