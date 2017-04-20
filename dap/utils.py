import json
import logging
import falcon

from sqlalchemy import exc
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend, BasicAuthBackend
from dap.db import LOCAL_CONN
from dap.user import User


log = logging.getLogger(__name__)


def user_loader(username, password):
    """Loads a user by its credentials."""
    with LOCAL_CONN.new_session() as session:
        user = User.auth(session, username, password)
        # Cannot use user object outside the session scope,
        # since the object has to be bound to a DB session.
        return {
            'id': user.id,
            'name': user.name,
            'db_addr': user.db_addr,
            'db_port': user.db_port,
            'db_pswd': user.db_pswd,
            'db_name': user.db_name
        }

jwt_backend = JWTAuthBackend(lambda payload: payload['user'], 'secretkey', verify_claims=['iat', 'exp'], required_claims=['iat', 'exp']) # TODO: use config
basic_backend = BasicAuthBackend(user_loader)
auth_middleware = FalconAuthMiddleware(jwt_backend)

class RequireJSON(object):

    def process_request(self, req, resp):
        if req.method in ('POST', 'PUT'):
            if not req.content_type or 'application/json' not in req.content_type:
                # TODO: change or remove link
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.',
                    href='http://docs.examples.com/api/json')


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
        raise falcon.HTTPForbidden('Access denied', description)
    elif code == 1054:
        raise falcon.HTTPBadRequest('Bad request', description)
    elif code == 1146:
        raise falcon.HTTPBadRequest('Bad request', description)
    else:
        description = ('Unspecified error')
        raise falcon.HTTPForbidden('Operational error', description)
