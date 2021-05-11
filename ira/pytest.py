from concurrent.futures import ThreadPoolExecutor

import pytest

from aiohttp import web

from ira.server import IraServer
from ira.client import IraClient


class IraContext:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return '<Ira({})>'.format(
            ', '.join([
                '{}={}'.format(key, repr(value))
                for key, value in self.kwargs.items()
            ])
        )

    async def await_browser_connected(self):
        future = self.ira_server.await_browser_connected()

        if future.done():
            return

        self.printer(
            'waiting for browser (http://{}:{}/ira/)'.format(
                self.host,
                self.port,
            )
        )

        await future

        self.printer('browser connected')


@pytest.fixture(scope='session')
def thread_pool_executor():
    return ThreadPoolExecutor(
        max_workers=10,
    )


@pytest.fixture
async def ira_context(aiohttp_server, loop, thread_pool_executor, printer):
    host = 'localhost'
    port = 9000
    app = web.Application()

    ira_server = IraServer(app=app)

    ira_server.set_loop(loop)
    ira_server.set_executor(thread_pool_executor)

    setup = aiohttp_server(app=app, port=port)

    return IraContext(
        host=host,
        port=port,
        app=app,
        loop=loop,
        executor=thread_pool_executor,
        printer=printer,
        ira_server=ira_server,
        setup=lambda: setup,
    )
