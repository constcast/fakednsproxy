#!/usr/bin/env python3

import sys
from core.main import FakeDnsProxy
from core.observer import createLoggerObserver

from twisted.logger import globalLogBeginner


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <config_file>".format(sys.argv[0]))
        sys.exit(1)
    srv = FakeDnsProxy(sys.argv[1])
    observer = createLoggerObserver(sys.stdout)
    globalLogBeginner.beginLoggingTo([observer])
    srv.run()
