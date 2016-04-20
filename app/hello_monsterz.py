from flask import Flask, Response, request, render_template
import requests
import hashlib
import redis
import html
from os import environ
import sys

app = Flask(__name__)
cache = redis.StrictRedis(host='redis', port=6379, db=0)
salt = sys.version

# We have a couple options here, default is to use `$HOSTNAME`
name = environ['HOSTNAME']
try:
    environ['USE_IP_ADDR']
    import socket
    name = socket.gethostbyname(socket.gethostname())
except KeyError:
    pass

# Count hits in Redis
def hit_me(name):

    counter = 'hits-{0}'.format(name)
    cache.incr(counter)

    return int(cache.get(counter))

def hex_me(name):
    return hashlib.sha256(name.encode()).hexdigest()

# Try to get best match for each visitor
def friend(request, hits):
    return '{0} [#{1}]'.format(request.headers.get('User-Agent'), hits)

@app.route('/')
def main_page():

    hits = hit_me(name)
    friend_hash = hex_me(friend(request, hits))

    return render_template('index.html', name=name, hits=hits,
        name_hash=hex_me(salt+name), friend_hash=friend_hash,
        friend_hash_short=friend_hash[:6])

@app.route('/monster/<name>')
def get_monster(name):

    if request.args.get('no_cache') is None:
        name = html.escape(name, quote=True)
        image = cache.get(name)
        if image is None:
            print('Cache miss', flush=True)
            r = requests.get('http://monsterz-den:8080/monster/' + name + '?size=80')
            image = r.content
            cache.set(name, image)
    else:
        r = requests.get('http://monsterz-den:8080/monster/' + name + '?size=80')
        image = r.content


    return Response(image, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9090)
