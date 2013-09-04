import moznetwork
import mozhttpd
import sys
import os
import json

if len(sys.argv) != 2:
    print "Usage: %s <dir>" % sys.argv[0]

@mozhttpd.handlers.json_response
def index(request):
    return (200, json.loads(open(os.path.join(sys.argv[1], 'index')).read()))

@mozhttpd.handlers.json_response
def package(request, packagename):
    return (200, json.loads(open(os.path.join(sys.argv[1], packagename,
                                              'index.json')).read()))


httpd = mozhttpd.MozHttpd(host=moznetwork.get_ip(), port=8888, docroot=sys.argv[1],
                          urlhandlers = [ { 'method': 'GET',
                                            'path': '/index/?$',
                                            'function': index },
                                          { 'method': 'GET',
                                            'path': '/([^/]+)/?$',
                                            'function': package } ])
print "Serving '%s' at %s:%s" % (httpd.docroot, httpd.host, httpd.port)
httpd.start(block=True)
