#!/usr/bin/env python3
import sys

from lib.account import Account

def set_up(arguments):
    if len(arguments) == 3:
        username = arguments[1]
        password = arguments[2]

        account = Account(username, password)
        account.get_flights()


if __name__ == "__main__":
    arguments = sys.argv

    try:
        set_up(arguments)
    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Stopping all checkins")
        sys.exit()
