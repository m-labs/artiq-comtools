import os
import sys
import unittest
import logging
import asyncio
import contextlib

from sipyco.pc_rpc import AsyncioClient

from artiq_comtools.ctlmgr import Controllers


logger = logging.getLogger(__name__)


class UnexpectedLogMessageError(Exception):
    pass


class FailingLogHandler(logging.Handler):
    def emit(self, record):
        raise UnexpectedLogMessageError("Unexpected log message: '{}'".format(
            record.getMessage()))


@contextlib.contextmanager
def expect_no_log_messages(level, logger=None):
    """Raise an UnexpectedLogMessageError if a log message of the given level
    (or above) is emitted while the context is active.

    Example: ::

        with expect_no_log_messages(logging.ERROR):
            do_stuff_that_should_not_log_errors()
    """
    if logger is None:
        logger = logging.getLogger()
    handler = FailingLogHandler(level)
    logger.addHandler(handler)
    try:
        yield
    finally:
        logger.removeHandler(handler)


class ControllerCase(unittest.TestCase):
    def setUp(self):
        if os.name == "nt":
            self.loop = asyncio.ProactorEventLoop()
        else:
            self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.addCleanup(self.loop.close)

        self.controllers = Controllers()
        self.controllers.host_filter = "::1"
        self.addCleanup(
            self.loop.run_until_complete, self.controllers.shutdown())

    async def start(self, name, entry):
        self.controllers[name] = entry
        await self.controllers.queue.join()
        await self.wait_for_ping(entry["host"], entry["port"])

    async def get_client(self, host, port):
        remote = AsyncioClient()
        await remote.connect_rpc(host, port, None)
        targets, _ = remote.get_rpc_id()
        await remote.select_rpc_target(targets[0])
        self.addCleanup(self.loop.run_until_complete, remote.close_rpc())
        return remote

    async def wait_for_ping(self, host, port, retries=5, timeout=2):
        dt = timeout/retries
        while timeout > 0:
            try:
                remote = await self.get_client(host, port)
                ok = await asyncio.wait_for(remote.ping(), dt)
                if not ok:
                    raise ValueError("unexcepted ping() response from "
                                     "controller: `{}`".format(ok))
                return ok
            except asyncio.TimeoutError:
                timeout -= dt
            except (ConnectionAbortedError, ConnectionError,
                    ConnectionRefusedError, ConnectionResetError):
                await asyncio.sleep(dt)
                timeout -= dt
        raise asyncio.TimeoutError

    async def start_dummy_controller(self, environment_overrides=None):
        entry = {
            "type": "controller",
            "host": "::1",
            "port": 1068,
            "command": (sys.executable.replace("\\", "\\\\")
                        + " -m artiq_comtools.test.dummy_controller "
                        + "-p {port}")
        }
        if environment_overrides is not None:
            entry["environment"] = environment_overrides
        await self.start("dummy_controller", entry)
        return await self.get_client(entry["host"], entry["port"])

    def test_start_ping_stop_controller(self):
        async def test():
            remote = await self.start_dummy_controller()
            await remote.ping()

        self.loop.run_until_complete(test())

    def test_start_controller_with_environment_override(self):
        async def test():
            env = {"TOTALLY_UNIQUE_TEST_ENV_VAR": "42"}
            remote = await self.start_dummy_controller(env)
            remote_env = await remote.get_os_environ()
            assert set(env.items()).issubset(set(remote_env.items()))

        self.loop.run_until_complete(test())

    def test_no_command_controller(self):
        entry = {
            "type": "controller",
            "host": "::1",
            "port": 1068
        }
        with expect_no_log_messages(logging.ERROR):
            self.controllers["corelog"] = entry
            self.assertTrue(self.controllers.queue.empty())
