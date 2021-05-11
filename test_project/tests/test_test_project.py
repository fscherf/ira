from concurrent.futures import ThreadPoolExecutor

from aiohttp.web import Application, Response
import pytest


class Server:
    HTML = """
        <html>
            <head>
                <style>
                    .square {
                        float: left;
                        margin: 3px;
                        width: 50px;
                        height: 50px;
                        cursor: pointer;
                        background-color: navy;
                    }

                    .maroon {
                        background-color: maroon !important;
                    }
                </style>
            </head>
            <body>
                <h1>Test View</h1>
                <div class="square"></div>
                <div class="square"></div>
                <div class="square"></div>
                <div class="square"></div>
                <div class="square"></div>

                <script>
                    document.querySelectorAll('.square').forEach(function(node) {
                        node.onclick = function(event) {
                            if(node.classList.contains('maroon')) {
                                node.classList.remove('maroon');

                            } else {
                                node.classList.add('maroon');
                            };
                        };
                    });
                </script>
            </body>
        </html>
    """

    def __init__(self, loop):
        self.loop = loop
        self.executor = ThreadPoolExecutor(max_workers=4)

        self.app = Application()
        self.app.router.add_route('*', '/test-view/', self.handle_request)

    async def handle_request(self, request):
        def _handle_request():
            return Response(
                body=self.HTML,
                content_type='text/html',
            )

        return await self.loop.run_in_executor(self.executor, _handle_request)


@pytest.fixture
def test_server(loop):
    return Server(loop=loop)


@pytest.fixture
def ira(ira_base, test_server):
    ira_base.ira_server.set_proxy_app(test_server.app)

    return ira_base


async def test_test_project(ira):
    import asyncio

    await asyncio.sleep(10)
