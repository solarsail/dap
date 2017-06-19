import json
import logging
import falcon

from sqlalchemy import exc
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend, BasicAuthBackend
from dap.db import LOCAL_CONN
from dap.user import User
from dap.config import CONF
from dap import exceptions


log = logging.getLogger(__name__)


def init_superuser(username, password):
    user = User.new(name=username, pswd=password, db_addr='127.0.0.1', db_port=3306, db_name='dapadmin_db', is_admin=True)
    with LOCAL_CONN.new_session() as session:
        session.add(user)


def user_loader(username, password):
    """Loads a user by its credentials."""
    with LOCAL_CONN.new_session() as session:
        user = User.auth(session, username, password)
        if not user:
            raise falcon.HTTPForbidden("Login failed", "Invalid username or password")
        # Cannot use user object outside the session scope,
        # since the object has to be bound to a DB session.
        return {
            'id': user.id,
            'name': user.name,
            'db_addr': user.db_addr,
            'db_port': user.db_port,
            'db_pswd': user.db_pswd,
            'db_name': user.db_name,
            'is_admin': user.is_admin
        }

jwt_backend = JWTAuthBackend(lambda payload: payload['user'], CONF['token']['secret'], verify_claims=['iat', 'exp'], required_claims=['iat', 'exp'])
basic_backend = BasicAuthBackend(user_loader)
auth_middleware = FalconAuthMiddleware(jwt_backend)

class RequireJSON(object):

    def process_request(self, req, resp):
        if req.method in ('POST', 'PUT'):
            if not req.content_type or 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.')


class JSONTranslator(object):

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0):
            # Nothing to do
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.context['doc'] = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource):
        if 'result' not in resp.context:
            return

        resp.body = json.dumps(resp.context['result'])


def handle_db_exception(ex, req, resp, params):
    log.exception(ex)
    code, description = ex.orig
    if code == 1045:
        description = ('Cannot connect to database')
        raise exceptions.HTTPForbiddenError(description)
    elif code == 1054:
        raise exceptions.HTTPBadRequestError(description)
    elif code == 1146:
        raise exceptions.HTTPBadRequestError(description)
    else:
        description = ('Unspecified error')
        raise exceptions.HTTPForbiddenError(description)

def handle_sql_exception(ex, req, resp, params):
    if (type(ex) == exc.NoSuchTableError):
        log.warn("table not exist: {}".format(params))
        raise exceptions.HTTPBadRequestError("Table not exist")
