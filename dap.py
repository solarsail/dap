# -*- coding: utf-8 -*-

import logging
import logging.config
import falcon

from sqlalchemy import exc
from dap.utils import RequireJSON, JSONTranslator, auth_middleware, handle_db_exception, handle_sql_exception
from dap import api, logconf


logging.config.dictConfig(logconf.conf_dict)
log = logging.getLogger('dap.main')

app = falcon.API(middleware=[auth_middleware, RequireJSON(), JSONTranslator()])

app.add_error_handler(exc.DBAPIError, handle_db_exception)
app.add_error_handler(exc.SQLAlchemyError, handle_sql_exception)

app.add_route("/login", api.login)
app.add_route("/test", api.test)
app.add_route("/register", api.register)
app.add_route("/data/{table}", api.mysql_table)
app.add_route("/data/{table}/{id}", api.mysql_row)
