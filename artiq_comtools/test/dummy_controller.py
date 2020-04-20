#!/usr/bin/env python3

import argparse
import os

from sipyco.pc_rpc import simple_server_loop
from sipyco import common_args


class Dummy:
    def print(self, x):
        print(x)
        return 42

    def ping(self):
        return True

    def get_os_environ(self):
        return dict(os.environ)


def get_argparser():
    parser = argparse.ArgumentParser(
        description="Dummy controller for testing purposes")
    common_args.simple_network_args(parser, 1068)
    common_args.verbosity_args(parser)
    return parser


def main():
    args = get_argparser().parse_args()
    common_args.init_logger_from_args(args)
    simple_server_loop({"dummy": Dummy()},
                        common_args.bind_address_from_args(args), args.port)

if __name__ == "__main__":
    main()
