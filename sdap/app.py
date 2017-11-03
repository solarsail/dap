# -*- coding: utf-8 -*-

import logging
import logging.config
import falcon

#from werkzeug.contrib.profiler import ProfilerMiddleware
from sqlalchemy import exc
from sdap.utils import *
from sdap import api, logconf


logging.config.dictConfig(logconf.conf_dict)
log = logging.getLogger(__name__)

# middlewares
app = falcon.API(middleware=[RequireJSON(), StreamReader(), Logger(), ResponseCache(), JSONTranslator(), RequireAuth(), AdminCheck()])

# error handlers
app.add_error_handler(exc.DBAPIError, handle_db_exception)
app.add_error_handler(exc.InvalidRequestError, handle_sql_exception)
app.add_error_handler(exc.StatementError, handle_sql_exception)
app.add_error_handler(exc.OperationalError, handle_sql_exception)

# routes
app.add_route("/register", api.register)
app.add_route("/privilege/{app}", api.privilege)
app.add_route("/key/{app}", api.key_mgmt)
app.add_route("/data/{table}", api.mysql_table)
app.add_route("/data/{table}/{id}", api.mysql_row)
app.add_route("/count/{table}", api.mysql_count)

# profiling
#app = ProfilerMiddleware(app, sort_by=("cumulative",), restrictions=(.05,))
