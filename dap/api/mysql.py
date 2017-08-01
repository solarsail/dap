import logging
import falcon

from dap.user import user_db_engine


log = logging.getLogger(__name__)


def _select(engine, table, id=None):
    where = " WHERE id={}".format(id) if id else ""
    query = "SELECT * FROM {}{}".format(table, where)
    columns = engine.columns(table)
    with engine.new_session() as conn:
        result = conn.execute(query).fetchall()

    return [dict(zip(columns, r)) for r in result]


class RDBTableAccess(object):
    def on_get(self, req, resp, table):
        """Retrieve the entire table."""
        user = req.context['user']
        engine = user_db_engine(user)
        result = _select(engine, table)

        log.info("user [{}]: get table [{}]".format(user, table))
        resp.context['result'] = { 'result': 'ok', 'data': result }
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp, table):
        """Create a new row."""
        user = req.context['user']
        pairs = req.context['doc']
        keys = ','.join(pairs.keys())
        values = ','.join(["'{}'".format(v) for v in pairs.values()])
        engine = user_db_engine(user)
        query = "INSERT INTO {} ({}) VALUES ({})".format(table, keys, values)

        with engine.new_session() as conn:
            result = conn.execute(query)
            id = result.lastrowid

        resp.context['result'] = {'result': 'ok', 'id': id}
        resp.status = falcon.HTTP_201


class RDBRowAccess(object):
    def on_get(self, req, resp, table, id):
        """Retrieve a single row by id."""
        user = req.context['user']
        engine = user_db_engine(user)
        result = _select(engine, table, id)

        log.info("user [{}]: get row with id [{}] from table [{}]".format(user, id, table))
        resp.context['result'] = { 'result': 'ok', 'data': result }
        resp.status = falcon.HTTP_200

    def on_put(self, req, resp, table, id):
        """Update an existing row."""
        user = req.context['user']
        pairs = req.context['doc']
        pairs = ["{}='{}'".format(k, v) for k, v in pairs.items()]
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

