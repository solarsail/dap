# -*- coding: utf-8 -*-

import logging
import logging.config
import falcon

#from werkzeug.contrib.profiler import ProfilerMiddleware
from sqlalchemy import exc
from sdap.utils import RequireJSON, JSONTranslator, Logger, RequireAuth, AdminCheck, handle_db_exception, handle_sql_exception
from sdap import api, logconf


logging.config.dictConfig(logconf.conf_dict)
log = logging.getLogger(__name__)

app = falcon.API(middleware=[RequireJSON(), JSONTranslator(), Logger(), RequireAuth(), AdminCheck()])

app.add_error_handler(exc.DBAPIError, handle_db_exception)
app.add_error_handler(exc.InvalidRequestError, handle_sql_exception)

app.add_route("/register", api.register)
app.add_route("/privilege/{app}", api.privilege)
app.add_route("/key/{app}", api.key_mgmt)
app.add_route("/data/{table}", api.mysql_table)
app.add_route("/data/{table}/{id}", api.mysql_row)
app.add_route("/count/{table}", api.mysql_count)
#app = ProfilerMiddleware(app, sort_by=("cumulative",), restrictions=(.1,))
