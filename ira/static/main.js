function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
};

// JobQueue -------------------------------------------------------------------
JobQueue = function() {
    this._promises = [];

    this._lock = function() {
        var promise_resolve;

        var promise = new Promise(function(resolve, reject) {
            promise_resolve = resolve;
        });

        promise.resolve = promise_resolve;

        var new_array_length = this._promises.push(promise);

        if(new_array_length == 1) {
            promise.resolve();
        };

        return promise;
    };

    this._unlock = function() {
        this._promises.shift();

        if(this._promises.length > 0) {
            this._promises[0].resolve();
        };
    };

    this.add = async function(callback) {
        await this._lock();

        try {
            var promise = await callback();

            if(promise instanceof Promise) {
                await promise;
            };

        } finally {
            this._unlock();

        };
    };
};

function IraIframe(ira, iframe) {
    this.ira = ira;
    this.iframe = iframe;

    this.job_queue = new JobQueue();
    this._promise = undefined;

    this.iframe.ira = this.ira;
    this.iframe.ira_iframe = this;

    /* location ------------------------------------------------------------ */
    this.load = function(url) {
        this.iframe.contentWindow.location = url;
    };

    this.reload = function() {
        this.iframe.contentDocument.location.reload();
    };

    this.get_location = function() {
        return this.iframe.contentDocument.location;
    };

    /* aspect -------------------------------------------------------------- */
    this.resize = function(width, height) {
        this.iframe.width = width;
        this.iframe.height = height;
    };

    this.resize_smartphone = function() {
        this.resize('411px', '731px');
    };

    this.resize_tablet = function() {
        this.resize('768px', '1024px');
    };

    this.resize_desktop = function() {
        this.resize('1024px', '768px');
    };

    /* events -------------------------------------------------------------- */
    this.setup_promise = function() {
        var promise_resolve;

        var promise = new Promise(function(resolve, reject) {
            promise_resolve = resolve;
        });

        promise.resolve = promise_resolve;
        this._promise = promise;

        return this._promise;
    };

    this.resolve_promise = function(data) {
        if(this._promise === undefined) {
            return;
        };

        this._promise.resolve(data);

        this._promise = undefined;
    };

    /* commands ------------------------------------------------------------ */
    this._handle_command = async function(args) {
        var return_value = {
            exit_code: 0,
        };

        if(args[0] == 'load') {
            var promise = this.setup_promise();

            this.load(args[1]);

            await promise;

        } else if(args[0] == 'reload') {
            var promise = this.setup_promise();

            this.reload();

            await promise;

        } else if(args[0] == 'enter') {
            var selector = args[1];
            var index = args[2];
            var value = args[3];
            var animation = args[4];

            if(index === undefined || index === null) {
                index = 0;
            };

            var nodes = this.iframe.contentDocument.querySelectorAll(selector);
            var node = nodes[index];

            if(animation) {
                await this.ira.click_node(node);

                node.value = value;

                await sleep(1000);

            } else {
                node.value = value;
            };

            var event = new Event('change');

            node.dispatchEvent(event);

        } else if(args[0] == 'click') {
            var selector = args[1];
            var index = args[2];
            var animation = args[3];

            if(index === undefined || index === null) {
                index = 0;
            };

            var nodes = this.iframe.contentDocument.querySelectorAll(selector);
            var node = nodes[index];

            if(animation) {
                await this.ira.click_node(node, function() {
                    node.click();
                });

            } else {
                node.click();

            };

        } else if(args[0] == 'get_html') {
            var selector = args[1];
            var index = args[2];

            if(index === undefined || index === null) {
                index = 0;
            };

            var nodes = this.iframe.contentDocument.querySelectorAll(selector);
            var node = nodes[index];

            return_value['result'] = node.innerHTML;
        };

        return return_value;
    };

    this.handle_command = async function(args) {
        var ira = this.ira;
        var ira_iframe = this;

        this.job_queue.add(async function() {
            var result = await ira_iframe._handle_command(args);

            ira.send(JSON.stringify(result));
        });
    };

    /* setup --------------------------------------------------------------- */
    this.resize_desktop();

    this.iframe.onload = function(event) {
        this.ira_iframe.resolve_promise(event);
    };
};


function Ira(selector) {
    this.selector = selector;

    this.handle_websocket_message = function(event) {
        var message = JSON.parse(event.data);

        console.log('ira <<', message);

        this.ira.ira_iframe.handle_command(message);
    };

    this.connect = function() {
        // setup websocket
        var protocol = 'ws://';

        if(window.location.protocol == 'https:') {
            protocol = 'wss://';
        }

        this._ws = new WebSocket(
            protocol + window.location.host + window.location.pathname);

        this._ws.ira = this;
        this._ws.onmessage = this.handle_websocket_message;
        this._ws.onclose = this.reconnect;
        this._ws.onopen = this.onopen;
    };

    this.reconnect = function() {
        setTimeout(function() {
            this.ira.connect();
        }, 1000);
    };

    this.send = function(message) {
        console.log('ira >>', message);

        this._ws.send(message);
    };

    this.onopen = function() {
        this.ira.reset();
    };

    this.reset = function() {
        // clear root node
        this.root_node = document.querySelector(this.selector);
        this.root_node.innerHTML = '';

        // setup iframe
        var iframe = document.createElement('iframe');
        this.root_node.appendChild(iframe);
        
        // setup ira iframe
        this.ira_iframe = new IraIframe(this, iframe);
    };

    this.click_node = async function(node, callback) {
        var cursor = document.querySelector('img#cursor');

        // scroll node into view
        // this.ira_iframe.iframe.scrollIntoViewIfNeeded();
        // node.scrollIntoViewIfNeeded();

        await sleep(500);

        // place cursor
        var cursor_rect = cursor.getBoundingClientRect();
        var node_rect = node.getBoundingClientRect();
        var iframe_rect = this.ira_iframe.iframe.getBoundingClientRect();
        
        var x = (node_rect.left + iframe_rect.left +
                 (node_rect.width / 2) - (cursor_rect.width * 2));

        var y = (node_rect.top + iframe_rect.top +
                 (node_rect.height / 2) - (cursor_rect.height * 2));

        // animation
        cursor.style.display = 'block';

        await cursor.animate(
            {
                left: [cursor.style.left, x + 'px'],
                top:  [cursor.style.top, y + 'px'],
            },
            {
              easing: 'ease',
              duration: 300,
              fill: 'forwards',
            },
        );

        await sleep(500);

        await cursor.animate(
            {
                width: ['20px', '16px'],
            },
            {
              easing: 'ease',
              duration: 200,
            },
        );

        if(callback) {
            callback();
        };

        await sleep(1000);

        cursor.style.display = 'none';
    };

    // setup
    this.connect();
};


var ira = undefined;
var iframe = undefined;

window.onload = function(event) {
    ira = new Ira('#ira');
    iframe = ira.ira_iframe.iframe;
};
