import memcache
import requests
from flask import Flask


app = Flask(__name__)

# Create a memcache client using the most common client, python-memcached.  We
# don't do anything special: since this client uses the `socket` module
# directly, it will automatically benefit from gevent and behave cooperatively.
mc = memcache.Client(['localhost:11212'])


# Makes an HTTP request with `requests` to the sleepserver
@app.route('/sync')
def proxy():
    # Since requests relies on the `socket` module, it will also automatically
    # benefit from gevent's monkey patches.
    return requests.get('http://127.0.0.1:6000/').text


# Uses a TCP connection to the slow "memcached" server
@app.route('/cache')
def cache():
    return mc.get('foo') or ''


# Run the debug server with `python flask_proxy.py`.
# It's an interesting point of comparison. The debug server is completely
# serial: it fully responds to each request before moving on to the next one.
# There is no concurrency.
#
# To run with gunicorn and gevent:
#
# $ gunicorn -w 2 -k gevent -b "0:5500" flask_proxy:app
#
# You can leave `-w 2` or set to the number of cores in your machines. There is
# no benefit to setting it higher: these workers use coroutines for cooperative
# multitasking, each worker process will use as much CPU as it can.
#
# If you run `ab` with `-c` and `-n` equal to each other, at nearly any level
# your computer can handle, you should see the entire test take 2-2.25 seconds.
# If `-c` < `-n`, then it will take ceiling(`-n` / `-c`) * 2 seconds, since
# `ab` will wait for the first set of responses before continuing.
#
# To run with gunicorn and sync workers:
#
# $ gunicorn -w 9 -k sync -b "0:5500" flask_proxy:app
#
# These workers are all OS processes that, like the debug server, will process
# one request at a time. It's interesting to play with `ab` and the number of
# workers (`-w X`). As long as `ab`'s concurrency (`-c`) is less than `-w`, the
# time-per-request should stay at just about 2 seconds, and the total time for
# the test will be 2 * ceil(`-n` / `-c`) (the optimal result). But if `-c` is
# greater than `-w`, requests will start queuing up, waiting for a worker, and
# you'll see a distribution that skews higher and higher with more concurrent
# requests.
if __name__ == '__main__':
    app.run(debug=True)
