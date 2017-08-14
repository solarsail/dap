import logging
import falcon

from dap.user import user_db_engine


log = logging.getLogger(__name__)


def _select(engine, table, id=None, columns=None, start=None, limit=None):
    if start and limit and start.isdigit() and limit.isdigit():
        where = " WHERE id >= {} LIMIT {}".format(start, limit)
    elif id and id.isdigit():
        where = " WHERE id={}".format(id)
    else:
        where = ""

    if not columns:
        columns = engine.columns(table)

    sc = ','.join("`{}`".format(c) for c in columns) if type(columns) == list else columns
    if ';' in sc:
        raise exceptions.HTTPBadRequestError("Invalid columns: {}".format(sc))
    if ';' in table:
        raise exceptions.HTTPBadRequestError("Invalid table: {}".format(table))

    query = "SELECT {} FROM {}{}".format(sc, table, where)
    with engine.new_session() as conn:
        result = conn.execute(query).fetchall()

    return [dict(zip(columns, r)) for r in result]


class RDBTableCount(object):
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
    def on_get(self, req, resp, table):
        """Retrieve the entire table, with or without pagination."""
        user = req.context['user']
        columns = req.params['column'] if 'column' in req.params else None # columns to query
        start = req.params['start'] if 'start' in req.params else None     # pagination: start id
        limit = req.params['limit'] if 'limit' in req.params else None     # pagination: row limit
        log.info(req.params)
        engine = user_db_engine(user)
        result = _select(engine, table, columns=columns, start=start, limit=limit)

        pagi = " start from id {} limit {}".format(start, limit) if start and limit else ""
        log.info("user [{}]: get table [{}]{}".format(user['user'], table, pagi))
        resp.context['result'] = { 'result': 'ok', 'data': result }
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp, table):
        """Create new row(s)."""
        user = req.context['user']
        try:
            data = req.context['doc']
            keys = ','.join(["`{}`".format(c) for c in data['columns']])
            values = data['values']
        except KeyError:
            raise HTTPBadRequestError("Missing columns or values")

        if values:
            value_clause = []
            for value in values:
                value_clause.append(','.join(["'{}'".format(v) for v in value]))
            values = ','.join(["({})".format(v) for v in value_clause])
            engine = user_db_engine(user)
            query = "INSERT INTO {} ({}) VALUES {}".format(table, keys, values)

            with engine.new_session() as conn:
                result = conn.execute(query)
                count = result.rowcount
        else:
            ids = []

        resp.context['result'] = {'result': 'ok', 'count': count}
        resp.status = falcon.HTTP_201


class RDBRowAccess(object):
    def on_get(self, req, resp, table, id):
        """Retrieve a single row by id."""
        user = req.context['user']
        columns = req.params['column'] if 'column' in req.params else None
        engine = user_db_engine(user)
        result = _select(engine, table, id=id, columns=columns)

        log.info("user [{}]: get row with id [{}] from table [{}]".format(user['user'], id, table))
        resp.context['result'] = { 'result': 'ok', 'data': result }
        resp.status = falcon.HTTP_200

    def on_put(self, req, resp, table, id):
        """Update an existing row."""
        user = req.context['user']
        pairs = req.context['doc']
        pairs = ["`{}`='{}'".format(k, v) for k, v in pairs.items()]
        pairs = ','.join(pairs)
        engine = user_db_engine(user)
        query = "UPDATE {} SET {} WHERE id={}".format(table, pairs, id)

        with engine.new_session() as conn:
            result = conn.execute(query)

        resp.context['result'] = {'result': 'ok'}
        resp.status = falcon.HTTP_201

    def on_delete(self, req, resp, table, id):
        """Delete an existing row."""
        user = req.context['user']
        engine = user_db_engine(user)
        query = "DELETE FROM {} WHERE id={}".format(table, id)

        with engine.new_session() as conn:
            result = conn.execute(query)

        resp.context['result'] = {'result': 'ok'}
        resp.status = falcon.HTTP_200

