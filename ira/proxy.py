import asyncio

from aiohttp import ClientSession, WSMsgType

from aiohttp.web import WebSocketResponse, Response


class Proxy:
    def __init__(self, app, loop):
        self.app = app
        self.loop = loop

        self.app.router.add_route(
            '*', '/{path:.*}', self.handle_proxy_request)

    async def handle_websocket_client_connection(self, request, socket_pair):
        url = '{}/{}'.format(
            self.proxy_url,
            request.match_info['path'],
        )

        server_websocket = socket_pair[0]

        async with ClientSession() as client:
            async with client.ws_connect(url) as client_websocket:
                socket_pair[1] = client_websocket
                socket_pair[2].set_result(True)

                async for message in client_websocket:
                    if message.type == WSMsgType.TEXT:
                        try:
                            await server_websocket.send_str(message.data)

                        except ConnectionResetError:
                            break

                    elif message.type in (WSMsgType.CLOSED, WSMsgType.ERROR):
                        break

    async def handle_websocket_proxy_request(self, request):
        websocket = WebSocketResponse()

        await websocket.prepare(request)

        socket_pair = [websocket, None, asyncio.Future()]

        self.loop.create_task(
            self.handle_websocket_client_connection(request, socket_pair)
        )

        await socket_pair[2]
        client_websocket = socket_pair[1]

        # main loop
        try:
            async for message in websocket:
                if message.type == WSMsgType.TEXT:
                    await client_websocket.send_str(message.data)

                elif message.type in (WSMsgType.CLOSED, WSMsgType.ERROR):
                    break

        except asyncio.CancelledError:
            pass

        except ConnectionResetError:
            pass

        finally:
            await websocket.close()

        return websocket

    async def handle_proxy_request(self, request):
        # websocket
        if(request.method == 'GET' and
           request.headers.get('upgrade', '').lower() == 'websocket'):

            return await self.handle_websocket_proxy_request(request)

        url = '{}/{}'.format(
            self.proxy_url,
            request.match_info['path'],
        )

        # post
        # FIXME

        # get
        async with ClientSession() as client:
            async with client.get(url) as client_response:
                response = Response(
                    status=client_response.status,
                    body=await client_response.text(),
                    content_type=client_response.content_type,
                )

                for name, value in client_response.headers.items():
                    response.headers[name] = value

                return response
