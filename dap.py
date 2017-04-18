#!/usr/bin/python

import falcon
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend

app = falcon.API(middleware=[auth_middleware])
