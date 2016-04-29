from flask import Flask, Response, request, render_template
import requests
import hashlib
import redis
import html
from os import getenv
import sys
from socket import gethostbyname, gethostname

app = Flask(__name__)
salt = sys.version

# By default identity is derrived from `$HOSTNAME`
name = gethostname()
# However, in some cases IP works better (e.g. when used with Weave Net)
if getenv('USE_IP_ADDR'): name = gethostbyname(gethostname())

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

services = {
    'redis': {
        'host': getenv('REDIS_HOST', 'redis'),
        'port': getenv('REDIS_PORT', '6379'),
    },
    'monsterz-den': {
        'host': getenv('MONSTERZ_DEN_HOST', 'monsterz-den'),
        'port': getenv('MONSTERZ_DEN_PORT', '8080'),
    },
}

cache = redis.StrictRedis(db=0, **services['redis'])

@app.route('/')
def main_page():

    hits = hit_me(name)
    friend_hash = hex_me(friend(request, hits))

    return render_template('index.html', name=name, hits=hits,
        name_hash=hex_me(salt+name), friend_hash=friend_hash,
        friend_hash_short=friend_hash[:6])

@app.route('/monster/<name>')
def get_monster(name):

    name = html.escape(name, quote=True)
    monster = 'http://{host}:{port}/monster/{name}?size=80'.format(name=name, **services['monsterz-den'])

    if request.args.get('no_cache') is None:
        image = cache.get(name)
        if image is None:
            print('Cache miss', flush=True)
            r = requests.get(monster)
            image = r.content
            cache.set(name, image)
    else:
        r = requests.get(monster)
        image = r.content


    return Response(image, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9090)
