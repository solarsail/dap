import logging
import falcon
import base64

from sdap import cache
from sdap.user import user_db_engine
from sqlalchemy.sql import text
from sdap import config, exceptions
#from sdap.utils import do_cprofile


log = logging.getLogger(__name__)


#@do_cprofile
def _select(engine, table, id=None, columns=None, start=None, limit=None, where=None):
    if not columns:
        columns = engine.columns(table)
    if type(columns) != list:
        columns = [columns]
    sc = ','.join("`{}`".format(c) for c in columns)

    if ';' in sc:
        raise exceptions.HTTPBadRequestError("Invalid columns: {}".format(sc))
    if ';' in table:
        raise exceptions.HTTPBadRequestError("Invalid table: {}".format(table))

    scfr = "" if id else "SQL_CALC_FOUND_ROWS "
    query = "SELECT {}{} FROM {}".format(scfr, sc, table)
    sql_id = "WHERE id = :id"
    sql_page = "WHERE id >= :start LIMIT :limit"
    values = {}

    if start and limit:
        try:
            query = text(' '.join([query, sql_page]))
            values["start"] = int(start)
            values["limit"] = int(limit)
        except ValueError:
            raise exceptions.HTTPBadRequestError("Invalid start or limit parameter")
    elif id:
        try:
            query = text(' '.join([query, sql_id]))
            values["id"] = int(id)
        except ValueError:
            raise exceptions.HTTPBadRequestError("Invalid id")
    elif where:
        query = text(' '.join([query, "WHERE {}".format(where)]))

    log.debug("select: about to execute")
    with engine.new_session() as conn:
        result = conn.execute(query, values).fetchall()
        count = conn.execute("SELECT FOUND_ROWS()").fetchone()[0]

    return [dict(zip(columns, r)) for r in result], count


def _make_key(engine, table, columns, start, limit):
    if not columns:
        columns = engine.columns(table)
    columns = ','.join("`{}`".format(c) for c in sorted(columns)) if type(columns) == list else columns
    key = "{}|{}|{}|{}".format(table, columns, start, limit)
    return key


class RDBTableCount(object):
    #@do_cprofile
    def on_get(self, req, resp, table):
        """Get the number of rows."""
        user = req.context['user']
        engine = user_db_engine(user)
        query = "SELECT COUNT(id) FROM {}".format(table)
        with engine.new_session() as session:
            count = session.execute(query).fetchone()[0]

        resp.context['result'] = { 'result': 'ok', 'count': count }
        resp.status = falcon.HTTP_200


class RDBTableAccess(object):
    #@do_cprofile
    def on_get(self, req, resp, table):
        """Retrieve the entire table, with or without pagination."""
        user = req.context['user']
        columns = req.params['column'] if 'column' in req.params else None # columns to query
        start = req.params['start'] if 'start' in req.params else None     # pagination: start id
        limit = req.params['limit'] if 'limit' in req.params else None     # pagination: row limit
        where = base64.b64decode(req.params['where']) if 'where' in req.params else None     # query filters

        engine = user_db_engine(user)
        key = _make_key(engine, table, columns, start, limit)
        resp.context['cache_key'] = key
        if config.use_cache() and cache.contains_query(key):
            resp.context['cache_hit'] = True
            resp.status = falcon.HTTP_200
        else:
            result, count = _select(engine, table, columns=columns, start=start, limit=limit, where=where)

            if config.use_cache():
                resp.context['cache_miss'] = True
            resp.context['result'] = { 'result': 'ok', 'data': result, 'total': count }
            resp.status = falcon.HTTP_200

        pagi = " start from id {} limit {}".format(start, limit) if start and limit else ""
        log.info("user [{}]: get table({}) [{}]{}".format(user['user'], columns if columns else "*", table, pagi))

    def on_post(self, req, resp, table):
        """Create new row(s)."""
        user = req.context['user']
        try:
            data = req.context['doc']
            columns = data['columns']
            keys = ','.join(["`{}`".format(c) for c in columns])
            values_param = ','.join([":{}".format(c) for c in columns])
            values = data['values']
        except KeyError:
            raise HTTPBadRequestError("Missing columns or values")

        if values:
            values_input = []
            for value in values:
                #value_clause.append(','.join(["'{}'".format(v) for v in value]))
                values_input.append(dict(zip(columns, value)))
            #values = ','.join(["({})".format(v) for v in value_clause])
            engine = user_db_engine(user)
            query = "INSERT INTO {} ({}) VALUES ({})".format(table, keys, values_param)

            with engine.new_session() as conn:
                result = conn.execute(query, values_input)
                count = result.rowcount
            if config.use_cache():
                cache.invalidate_query_pattern("{}|*".format(table))
        else:
            count = 0

        resp.context['result'] = {'result': 'ok', 'count': count}
        resp.status = falcon.HTTP_201


class RDBRowAccess(object):
    def on_get(self, req, resp, table, id):
        """Retrieve a single row by id."""
        user = req.context['user']
        columns = req.params['column'] if 'column' in req.params else None
        engine = user_db_engine(user)
        key = _make_key(engine, table, columns, id, -1)
        resp.context['cache_key'] = key
        if config.use_cache() and cache.contains_query(key):
            resp.context['cache_hit'] = True
            resp.status = falcon.HTTP_200
        else:
            result, count = _select(engine, table, id=id, columns=columns)

            resp.context['cache_miss'] = True
            resp.context['result'] = { 'result': 'ok', 'data': result }
            resp.status = falcon.HTTP_200

        log.info("user [{}]: get row({}) with id [{}] from table [{}]".format(user['user'], columns if columns else "*", id, table))

    def on_put(self, req, resp, table, id):
        """Update an existing row."""
        user = req.context['user']
        pairs = req.context['doc']['values']
        keys = pairs.keys()
        set_clause = ["`{}`=:{}".format(k, k) for k in keys]
        set_clause = ','.join(set_clause)
        engine = user_db_engine(user)
        query = "UPDATE {} SET {} WHERE id=:id".format(table, set_clause)
        try:
            pairs['id'] = int(id)
        except ValueError:
            raise exceptions.HTTPBadRequestError("Invalid ID")

        with engine.new_session() as conn:
            result = conn.execute(query, pairs)

        if config.use_cache():
            key = _make_key(engine, table, columns, id, -1)
            cache.invalidate_query_pattern("{}".format(key))
        resp.context['result'] = {'result': 'ok'}
        resp.status = falcon.HTTP_200

    def on_delete(self, req, resp, table, id):
        """Delete an existing row."""
        user = req.context['user']
        engine = user_db_engine(user)
        query = "DELETE FROM {} WHERE id=:id".format(table)

        with engine.new_session() as conn:
            result = conn.execute(query, { "id": id })

        resp.context['result'] = {'result': 'ok'}
        resp.status = falcon.HTTP_200

