#!/usr/bin/env python3

import os
import sys
import config


def main():
    if os.geteuid() == 0 or os.getuid() == 0:
        sys.exit("You should not run this script as root.")

    m = config.load_config("config.json")

    m.run()


if __name__ == "__main__":
    main()
