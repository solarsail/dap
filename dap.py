#!/usr/bin/python

import falcon
import api

from falcon_auth import FalconAuthMiddleware, JWTAuthBackend
from utils import RequireJSON, JSONTranslator, auth_middleware


app = falcon.API(middleware=[auth_middleware, RequireJSON(), JSONTranslator()])

app.add_route("/login", api.login)
app.add_route("/test", api.test)
