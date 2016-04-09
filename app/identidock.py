from flask import Flask, Response, request
import requests
import hashlib
import redis
import html
import os

app = Flask(__name__)
cache = redis.StrictRedis(host='redis', port=6379, db=0)
salt = "UNIQUE_SALT"
name = os.environ['HOSTNAME']

try:
  os.environ['USE_IP_ADDR']
  import socket
  name = socket.gethostbyname(socket.gethostname())
except KeyError:
  pass

def hit_me(name):

    counter = 'hits-{0}'.format(name)
    cache.incr(counter)

    return int(cache.get(counter))

@app.route('/')
def mainpage():

    hits = hit_me(name)
    salted_name = salt + name
    name_hash = hashlib.sha256(salted_name.encode()).hexdigest()
    friend_name = '{0} [#{1}]'.format(request.headers.get('User-Agent'), hits)
    friend_hash = hashlib.sha256(friend_name.encode()).hexdigest()
    header = '<html><head><title>IdentiOrca</title></head><body>'
    body = '''<h2>Hello! My name is {0}.</h2>
              <p/>
              <strong><em>I have been seen {1} times.</em></strong>
              <p/>
              <img src="/monster/{2}"/>
              <p/>
              <strong><em>Also, please meet my random friend, {3}, who wants to talk to you!</em></strong>
              <p/>
              <img src="/monster/{3}?no_cache=1"/>
              '''.format(name, hits, name_hash, friend_hash[:6])
    footer = '</body></html>'

    return header + body + footer


@app.route('/monster/<name>')
def get_identicon(name):

    if request.args.get('no_cache') is None:
        name = html.escape(name, quote=True)
        image = cache.get(name)
        if image is None:
            print ("Cache miss", flush=True)
            r = requests.get('http://dnmonster:8080/monster/' + name + '?size=80')
            image = r.content
            cache.set(name, image)
    else:
        r = requests.get('http://dnmonster:8080/monster/' + name + '?size=80')
        image = r.content


    return Response(image, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
