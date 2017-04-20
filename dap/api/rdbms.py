import logging
import falcon

from sqlalchemy import exc
from sqlalchemy.sql import text
from dap.db import DBEngine
from dap.user import user_db_engine


log = logging.getLogger(__name__)

def _select(engine, table, id=None):
    where = " WHERE id={}".format(id) if id else ""
    query = "SELECT * FROM {}{}".format(table, where)
    try:
        columns = engine.columns(table)
        with engine.connect() as conn:
            result = conn.execute(query).fetchall()
    except exc.OperationalError as ex:
        log.exception(ex)
        code, description = ex.orig
        if code == 1045:
            description = ('Cannot connect to database')
            raise falcon.HTTPForbidden('Access denied', description)
        else:
            description = ('Unspecified error')
            raise falcon.HTTPForbidden('Database error', description)
    except Exception as ex:
        log.exception(ex)
        description = ('Invalid table name or id')
        raise falcon.HTTPServiceUnavailable('Data access error', description)

    return [dict(zip(columns, r)) for r in result]


class RDBTableAccess(object):
    def on_get(self, req, resp, table):
        """Retrieve the entire table."""
        user = req.context['user']
        engine = user_db_engine(user)
        result = _select(engine, table)

        resp.context['result'] = result
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp, table):
        """Create a new row."""
        user = req.context['user']
        pairs = req.context['doc']
        keys = ','.join(pairs.keys())
        values = ','.join(["'{}'".format(v) for v in pairs.values()])
        engine = user_db_engine(user)
        query = "INSERT INTO {} ({}) VALUES ({})".format(table, keys, values)

        try:
            with engine.connect() as conn:
                result = conn.execute(query)
        except exc.OperationalError as ex:
            log.exception(ex)

            code, description = ex.orig
            # distinguish among errors
            # TODO: extract error code handling
            if code == 1045:
                description = ('Cannot connect to database')
                raise falcon.HTTPForbidden('Access denied', description)
            elif code == 1054:
                raise falcon.HTTPInvalidParam(description, "column")
        except Exception as ex:
            log.exception(ex)
            description = ('Unspecified error')
            raise falcon.HTTPServiceUnavailable('Data access error', description)

        # TODO: return id
        resp.context['result'] = {'result': 'ok'}
        resp.status = falcon.HTTP_201


class RDBRowAccess(object):
    def on_get(self, req, resp, table, id):
        """Retrieve a single row by id."""
        user = req.context['user']
        engine = user_db_engine(user)
        result = _select(engine, table, id)

        resp.context['result'] = result
        resp.status = falcon.HTTP_200

    def on_put(self, req, resp, table, id):
        """Update an existing row."""
        user = req.context['user']
        pairs = req.context['doc']
        pairs = ["{}='{}'".format(k, v) for k, v in pairs.items()]
        pairs = ','.join(pairs)
        engine = user_db_engine(user)
        query = "UPDATE {} SET {} WHERE id={}".format(table, pairs, id)

        try:
            with engine.connect() as conn:
                result = conn.execute(query)
        except exc.OperationalError as ex:
            log.exception(ex)

            code, description = ex.orig
            # distinguish among errors
            # TODO: extract error code handling
            if code == 1045:
                description = ('Cannot connect to database')
                raise falcon.HTTPForbidden('Access denied', description)
            elif code == 1054:
                raise falcon.HTTPInvalidParam(description, "column")
        except Exception as ex:
            log.exception(ex)
            description = ('Unspecified error')
            raise falcon.HTTPServiceUnavailable('Data access error', description)

        resp.context['result'] = {'result': 'ok'}
        resp.status = falcon.HTTP_201

    def on_delete(self, req, resp, table, id):
        """Delete an existing row."""
        user = req.context['user']
        engine = user_db_engine(user)
        query = "DELETE FROM {} WHERE id={} CASCADE".format(table, id)

        try:
            with engine.connect() as conn:
                result = conn.execute(query)
        except exc.OperationalError as ex:
            log.exception(ex)

            code, description = ex.orig
            # distinguish among errors
            # TODO: extract error code handling
            if code == 1045:
                description = ('Cannot connect to database')
                raise falcon.HTTPForbidden('Access denied', description)
            elif code == 1054:
                raise falcon.HTTPInvalidParam(description, "column")
        except Exception as ex:
            log.exception(ex)
            description = ('Unspecified error')
            raise falcon.HTTPServiceUnavailable('Data access error', description)

        resp.context['result'] = {'result': 'ok'}
        resp.status = falcon.HTTP_200

