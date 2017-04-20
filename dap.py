# -*- coding: utf-8 -*-

import logging
import logging.config
import falcon

from falcon_auth import FalconAuthMiddleware, JWTAuthBackend
from dap.utils import RequireJSON, JSONTranslator, auth_middleware
from dap import api, logconf


logging.config.dictConfig(logconf.conf_dict)
log = logging.getLogger('dap.main')

app = falcon.API(middleware=[auth_middleware, RequireJSON(), JSONTranslator()])

app.add_route("/login", api.login)
app.add_route("/test", api.test)
app.add_route("/data/{table}", api.mysql_table)
app.add_route("/data/{table}/{id}", api.mysql_row)
# TODO: 404
