import logging
import falcon

import dap.utils

from sqlalchemy.orm import exc
from dap import exceptions
from dap.user import User
from dap.db import LOCAL_CONN
from dap.config import CONF, shared_db_name


log = logging.getLogger(__name__)

def _parse_priv(sql_result):
    # TODO: merge overlaped privileges on columns
    db = CONF['shared_db']['name']
    tables = LOCAL_CONN.tables(db)
    priv = { table: [] for table in tables }
    for grant in sql_result:
        grant = grant[0][6:]
        (p, r) = grant.split("ON")
        p = p.strip() # privilege
        t = r.split("TO")[0]
        t = t.split('.')[1].strip()[1:-1] # table

        if p.startswith("USAGE"):
            continue
        if p == "ALL PRIVILEGES":
            priv[t] = "all"
        else:
            priv[t].append(p)

    return priv


class Privilege(object):
    def on_get(self, req, resp, app):
        with LOCAL_CONN.new_session() as session:
            user = User.get_user(session, app)

            dbuser = user['user']
            result = session.execute("SHOW GRANTS FOR '{}'@'localhost'".format(dbuser)).fetchall()
            priv = _parse_priv(result)

        resp.status = falcon.HTTP_200
        resp.context['result'] = { 'result': 'ok', 'priv': priv }


    def on_post(self, req, resp, app):
        data = req.context['doc']

        required = ['priv']
        for field in required:
            if field not in data.keys():
                raise exceptions.HTTPMissingParamError(field)

        db = shared_db_name()
        sqls = []
        with LOCAL_CONN.new_session() as session:
            user = User.get_user(session, app)

        dbuser = user['user']
        priv = data['priv']
        try:
            for table_priv in priv:
                table = table_priv['table']
                perms = table_priv['perms']
                for perm in perms:
                    column = perm['column']
                    access = perm['access']
                    grant = []
                    if 'insert' in access:
                        grant.append('INSERT')
                    if 'select' in access:
                        grant.append('SELECT')
                    # FIXME other permissions
                    priv_clause = ','.join(grant)
                    column_clause = "" if column == "_all_" else "({})".format(column)
                    sql = "GRANT {} ON {}.{} {} TO '{}'@'localhost'".format(priv_clause, db, table, column_clause, dbuser) # FIXME escape the query
                    sqls.append(sql)
        except KeyError as e:
            raise exceptions.HTTPMissingParamError(e)

        with LOCAL_CONN.new_session() as session:
            for sql in sqls:
                session.execute(sql)

        resp.status = falcon.HTTP_200
        resp.context['result'] = { 'result': 'ok' }


