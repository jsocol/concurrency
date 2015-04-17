import argparse
import memcache
from tornado import gen, httpclient, httpserver, ioloop, web


UPSTREAM = 'http://localhost:6000/'


class SyncStyleProxy(web.RequestHandler):
    def initialize(self):
        self.client = httpclient.AsyncHTTPClient()

    # `@gen.coroutine` is the new `@web.asynchronous`. It technically uses
    # Futures under the hood and *can* (though not necessarily *should*) work
    # with `concurrent.futures` and the process- and thread-pool executors.
    #
    # With `@gen.coroutine`, instead of breaking your handler up into
    # callbacks, you can write code that looks much more straight-forward and
    # looks synchronous, except for the occasional `yield` statement.
    #
    # You can still make concurrent (and often truly parallel!) requests, by
    # `yield`ing multiple futures at once, which is the chief advantage of
    # Tornado over other Python options.
    @gen.coroutine
    def get(self):
        r = yield self.client.fetch(UPSTREAM)
        self.write(r.body)


class AsyncStyleProxy(web.RequestHandler):
    def initialize(self):
        self.client = httpclient.AsyncHTTPClient()

    # `@web.asynchronous` is how we used to write Tornado code. Reasoning about
    # callbacks is a pain, and we'd often need to use `functools.partial` to
    # create a callback with the variables we needed from the current scope.
    # `@gen.coroutine` is much nicer and more modern. Unless you have a *very
    # good reason*, you should use it.
    @web.asynchronous
    def get(self):
        self.client.fetch(UPSTREAM, callback=self._finish)

    def _finish(self, r):
        self.write(r.body)


class BlockingProxy(web.RequestHandler):
    def initialize(self):
        self.client = httpclient.HTTPClient()

    def get(self):
        # Don't do this!
        # No `yield`, and using the "sync" HTTP client. This will block the
        # Tornado event loop, and the current process will not be able to
        # handle any other requests. c.f. the `sync` gunicorn worker in
        # `flask_proxy.py`.
        r = self.client.fetch(UPSTREAM)
        self.write(r.body)


class CacheProxy(web.RequestHandler):
    def initialize(self):
        self.mc = memcache.Client(['localhost:11212'])

    def get(self):
        r = self.mc.get('foo')
        self.write(r)


app = web.Application([
    web.url(r'^/sync$', SyncStyleProxy),
    web.url(r'^/async$', AsyncStyleProxy),
    web.url(r'^/block$', BlockingProxy),
    web.url(r'^/cache$', CacheProxy),
])


def get_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start', help='use bind/start',
                        action='store_true')
    parser.add_argument('-m', '--max-clients', type=int, default=100)
    return parser.parse_args()


if __name__ == '__main__':
    options = get_options()
    httpclient.AsyncHTTPClient.configure(None, max_clients=options.max_clients)
    server = httpserver.HTTPServer(app)
    print 'Listening on 0:5500'
    print '/sync - coroutine proxy'
    print '/async - callback proxy'
    print '/block - ioloop-blocking proxy'
    print '/cache - hit "memcached"'
    if options.start:
        server.bind(5500)
        server.start(0)
    else:
        server.listen(5500)
    ioloop.IOLoop.instance().start()
