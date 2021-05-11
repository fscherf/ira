import asyncio
import hashlib
import logging
import time
import os

from aiohttp import WSMsgType

from aiohttp.web import (
    WebSocketResponse,
    json_response,
    FileResponse,
    Response,
)

logger = logging.getLogger('ira')

TEMPLATE_ROOT = os.path.join(
    os.path.dirname(__file__),
    'templates',
)

FRONTENT_HTML = os.path.join(
    TEMPLATE_ROOT,
    'frontend.html',
)

STATIC_ROOT = os.path.join(
    os.path.dirname(__file__),
    'static',
)


class IraServer:
    def __init__(self, app):
        self.app = app
        self._loop = None
        self._executor = None

        self.connections = {}
        self.pending_futures = {}
        self._pending_browser_connections = []

        self.app.on_shutdown.append(self.stop)

        # setup aiohttp routes
        logger.debug('setup aiohttp routing')

        self.app.router.add_route(
            '*', '/ira/static/{path:.*}', self.handle_static_file_request)

        self.app.router.add_route(
            '*', '/ira/token.json', self.handle_token_request)

        self.app.router.add_route(
            'POST', '/ira/{token}/rpc.json', self.handle_rpc_requests)

        self.app.router.add_route(
            '*', '/ira/', self.handle_frontend_request)

        self.app.router.add_route(
            '*', '/ira', self.handle_frontend_request)

    def set_loop(self, loop):
        self._loop = loop

    def set_executor(self, executor):
        self._executor = executor

    @property
    def loop(self):
        return self._loop

    @property
    def executor(self):
        return self._executor

    async def stop(self, *args, **kwargs):
        logger.debug('stop')

        for token, websocket in self.connections.copy().items():
            try:
                await websocket.close()

            except Exception:
                pass

    # asyncio helper ##########################################################
    def run_coroutine_sync(self, coroutine, wait=True):
        future = asyncio.run_coroutine_threadsafe(coroutine, loop=self.loop)

        if wait:
            return future.result()

        return future

    def run_function_async(self, function, *args, **kwargs):
        def _function():
            return function(*args, **kwargs)

        return self.loop.run_in_executor(self.executor, _function)

    # handle frontend #########################################################
    async def generate_token(self):
        def _generate_token():
            return hashlib.md5(str(time.monotonic_ns()).encode()).hexdigest()

        return await self.run_function_async(_generate_token)

    async def handle_static_file_request(self, request):
        def find_static_file():
            rel_path = request.match_info['path']

            abs_path = os.path.join(STATIC_ROOT, rel_path)
            file_exists = os.path.exists(abs_path)

            return file_exists, abs_path

        file_exists, path = await self.run_function_async(
            find_static_file,
        )

        if not file_exists:
            return Response(
                status=404,
                text='404: Not found',
            )

        return FileResponse(path)

    async def handle_frontend_websocket(self, request):
        token = await self.generate_token()
        websocket = WebSocketResponse()

        await websocket.prepare(request)

        self.connections[token] = websocket

        if self._pending_browser_connections:
            future = self._pending_browser_connections.pop(0)

            future.set_result(True)

        # main loop
        try:
            async for message in websocket:
                if message.type == WSMsgType.TEXT:
                    if(token not in self.pending_futures or
                       self.pending_futures[token].done() or
                       self.pending_futures[token].cancelled()):

                        continue

                    self.pending_futures[token].set_result(message.data)

                elif message.type in (WSMsgType.CLOSED, WSMsgType.ERROR):
                    break

        except asyncio.CancelledError:
            pass

        except ConnectionResetError:
            pass

        finally:
            self.connections.pop(token)

            await websocket.close()

        return websocket

    async def handle_frontend_request(self, request):
        # websocket
        if(request.method == 'GET' and
           request.headers.get('upgrade', '').lower() == 'websocket'):

            return await self.handle_frontend_websocket(request)

        response = FileResponse(FRONTENT_HTML)

        return response

    # rpc #####################################################################
    async def handle_token_request(self, request):
        data = {
            'exit_code': 0,
            'token': '',
        }

        for token, connection in self.connections.items():
            data['token'] = token

            return json_response(data)

        data['exit_code'] = 1

        return json_response(data)

    async def handle_rpc_requests(self, request):
        data = {
            'exit_code': 1,
        }

        token = request.match_info['token']

        if token not in self.connections:
            data['exit_code'] = 1

        else:
            post_data = await request.post()

            self.pending_futures[token] = asyncio.Future()

            try:
                await self.connections[token].send_str(post_data['data'])

            except ConnectionResetError:
                return json_response(data)

            try:
                await asyncio.wait_for(
                    self.pending_futures[token],
                    timeout=10,
                )

                json_data = self.pending_futures[token].result()

                return Response(body=json_data)

            finally:
                self.pending_futures.pop(token)

        return json_response(data)

    # pytest helper ###########################################################
    def await_browser_connected(self):
        future = asyncio.Future(loop=self.loop)

        if self.connections:
            future.set_result(True)

        else:
            self._pending_browser_connections.append(future)

        return future
