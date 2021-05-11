from argparse import ArgumentParser
import asyncio
import logging
import signal
import code
import os

from aiohttp.web import Application, run_app

from ira.server import IraServer

try:
    import IPython

    IPYTHON = True

except ImportError:
    IPYTHON = False


def run_server(args):
    loop = asyncio.get_event_loop()

    # parse command line
    parser = ArgumentParser()

    parser.add_argument(
        'proxy_url',
        type=str,
        default='http://localhost:8080',
    )

    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=9000)
    parser.add_argument('--shutdown-timeout', type=float, default=0.0)
    parser.add_argument('--shell', action='store_true')

    parser.add_argument(
        '-l', '--log-level',
        choices=['debug', 'info', 'warn', 'error', 'critical'],
        default='warn',
    )

    cli_args = parser.parse_args(args)

    # setup logging
    logging.basicConfig(level={
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARN,
        'error': logging.ERROR,
        'critical': logging.CRITICAL,
    }[cli_args.log_level.lower()])

    # setup ira server
    app = Application()

    server = IraServer(
        proxy_url=cli_args.proxy_url,
        proxy_app=None,
        app=app,
        loop=loop,
    )

    app['server'] = server

    async def shutdown(app):
        print('stopping server')

        await server.stop()

    app.on_shutdown.append(shutdown)

    # run server
    if cli_args.shell:
        async def start_shell(server):
            def _start_shell():
                if IPYTHON:
                    IPython.embed(
                        locals={'server': server},
                    )

                else:
                    code.interact(
                        local={'server': server},
                    )

                os.kill(os.getpid(), signal.SIGTERM)

            loop.run_in_executor(None, _start_shell)

        loop.create_task(start_shell(server))

    run_app(
        app=app,
        host=cli_args.host,
        port=cli_args.port,
        shutdown_timeout=cli_args.shutdown_timeout,
    )
