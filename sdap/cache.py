import pickle
import redis

from config import CONF

_conf = CONF['redis']
_conn = redis.StrictRedis(host=_conf['addr'], port=_conf['port'], db=0)
_conn.flushall()


def contains_query(query):
    exists = _conn.exists(query)
    return exists

def cached_query(query):
    cached = _conn.get(query)
    return cached

def invalidate_query(query):
    _conn.delete(query)

def set_query(query, records):
    _conn.set(query, records)
