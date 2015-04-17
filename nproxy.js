var http = require('http');
var mc = require('mc');

var UPSTREAM = 'http://localhost:6000/';
var CACHE = '127.0.0.1:11212';

// This is not idiomatic node, and not the best way to do this. It is
// implemented this way for direct comparison.
function proxyRequest(req, res) {
    console.log('got req');
    req.on('data', function() {});
    req.on('end', function() {});
    if (req.url == '/async') {
        http.get(UPSTREAM, function(pres) {
            var data = '';
            pres.on('data', function(chunk) { data += chunk; });
            pres.on('end', function() {
                res.end(data);
            });
        });
    } else if(req.url == '/cache') {
        var cache = new mc.Client(CACHE);
        cache.connect(function() {
            cache.get('foo', function(err, resp) {
                if (err) {
                    console.log(err);
                    res.writeHead(503);
                    res.end();
                    return;
                }
                res.end(resp['foo']);
            });
        });
    } else {
        res.writeHead(404);
        res.end('404 lol');
    }
}

var server = http.createServer(proxyRequest);
server.listen(5700);
console.log("Listening on :5700");
