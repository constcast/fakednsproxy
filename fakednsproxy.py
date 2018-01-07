#!/usr/bin/env python3

import sys
from core.main import FakeDnsProxy

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <config_file>".format(sys.argv[0]))
        sys.exit(1)
    srv = FakeDnsProxy(sys.argv[1])
    srv.run()
