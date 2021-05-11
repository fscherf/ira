import json
import os

import requests


class IraClient:
    def __init__(self, host):
        self.host = host
        self.animations = False

        self.token_end_point = os.path.join(
            self.host,
            'ira/token.json',
        )

        self.get_token()

    def __repr__(self):
        return '<IraClient(host={}, token={})>'.format(
            repr(self.host),
            repr(self.token),
        )

    def get_token(self):
        response = requests.get(self.token_end_point)

        if response.status_code != 200:
            self.token = ''
            self.rpc_end_point = ''

            return

        json = response.json()

        if json['exit_code'] != 0:
            self.token = ''
            self.rpc_end_point = ''

            return

        self.token = json['token']

        self.rpc_end_point = os.path.join(
            self.host,
            'ira',
            self.token,
            'rpc.json',
        )

    def rpc_request(self, data):
        response = requests.post(
            self.rpc_end_point,
            {'data': json.dumps(data)},
        )

        return response.json()

    def load(self, url):
        return self.rpc_request(['load', url])

    def reload(self):
        return self.rpc_request(['reload'])

    def enter(self, selector, value, index=None, animation=None):
        if animation is None:
            animation = self.animations

        return self.rpc_request(['enter', selector, index, value, animation])

    def click(self, selector, index=None, animation=None):
        if animation is None:
            animation = self.animations

        return self.rpc_request(['click', selector, index, animation])

    def get_html(self, selector, index=None):
        return self.rpc_request(['get_html', selector, index])


if __name__ == '__main__':
    import time

    c = IraClient('http://localhost:8080')

    def test_click_events():
        c.load('/')
        c.click('a', 26, animation=True)

        for i in range(0, 5):
            c.click('.lona-clickable', i, animation=True)

        time.sleep(2)

        c.load('/')

    import IPython
    IPython.embed()
