#!/usr/bin/env python3

import asyncio
import atexit
import argparse
import logging
import platform

from sipyco.pc_rpc import Server
from sipyco.logs import LogForwarder, SourceFilter
from sipyco import common_args
from sipyco.tools import atexit_register_coroutine, SignalHandler, SimpleSSLConfig

from artiq_comtools.ctlmgr import ControllerManager


def get_argparser():
    parser = argparse.ArgumentParser(description="ARTIQ controller manager")

    common_args.verbosity_args(parser)

    parser.add_argument(
        "-s", "--server", default="localhost",
        help="hostname or IP of the master to connect to")
    parser.add_argument(
        "--port-notify", default=3250, type=int,
        help="TCP port to connect to for notifications")
    parser.add_argument(
        "--port-logging", default=1066, type=int,
        help="TCP port to connect to for logging")
    parser.add_argument(
        "--ssl", nargs=3, metavar=('CERT', 'KEY', 'PEER'), default=None,
        help="Enable SSL for master connections: "
             "CERT: client certificate file, "
             "KEY: client private key, "
             "PEER: master certificate to trust "
             "(default: %(default)s)")
    parser.add_argument(
        "--retry-master", default=5.0, type=float,
        help="retry timer for reconnecting to master")
    parser.add_argument(
        "--host-filter", default=None, help="IP address of controllers to launch "
        "(local address of master connection by default)")
    common_args.simple_network_args(parser, [("control", "control", 3249)])
    return parser


def main():
    args = get_argparser().parse_args()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.NOTSET)
    source_adder = SourceFilter(logging.WARNING +
                                args.quiet*10 - args.verbose*10,
                                "ctlmgr({})".format(platform.node()))
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "%(levelname)s:%(source)s:%(name)s:%(message)s"))
    console_handler.addFilter(source_adder)
    root_logger.addHandler(console_handler)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    atexit.register(loop.close)
    signal_handler = SignalHandler()
    signal_handler.setup()
    atexit.register(signal_handler.teardown)
    ssl_config = SimpleSSLConfig(*args.ssl) if args.ssl else None

    logfwd = LogForwarder(args.server, args.port_logging,
                          args.retry_master, ssl_config=ssl_config)
    logfwd.addFilter(source_adder)
    root_logger.addHandler(logfwd)
    logfwd.start()
    atexit_register_coroutine(logfwd.stop)

    ctlmgr = ControllerManager(args.server, args.port_notify,
                               args.retry_master, args.host_filter,
                               loop=loop, ssl_config=ssl_config)
    ctlmgr.start()
    atexit_register_coroutine(ctlmgr.stop)

    class CtlMgrRPC:
        retry_now = ctlmgr.retry_now

    rpc_target = CtlMgrRPC()
    rpc_server = Server({"ctlmgr": rpc_target}, builtin_terminate=True)
    loop.run_until_complete(rpc_server.start(common_args.bind_address_from_args(args),
                                             args.port_control))
    atexit_register_coroutine(rpc_server.stop)

    print("ARTIQ controller manager is now running.")
    _, pending = loop.run_until_complete(asyncio.wait(
        [loop.create_task(signal_handler.wait_terminate()),
         loop.create_task(rpc_server.wait_terminate())],
        return_when=asyncio.FIRST_COMPLETED))
    for task in pending:
        task.cancel()


if __name__ == "__main__":
    main()
