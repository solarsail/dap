import json
import logging
import random
import string
import falcon
import cProfile
import pstats

from sqlalchemy import exc
from sdap.db import LOCAL_CONN
from sdap.user import User
from sdap import exceptions


log = logging.getLogger(__name__)


def do_cprofile(func):
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable
            return result
        finally:
            #profile.dump_stats("profile.log")
            ps = pstats.Stats(profile).sort_stats("cumulative")
            ps.print_stats(.03)
    return profiled_func


def init_superuser():
    """Initializes the admin user."""
    user = User.new(app="__dap_admin", desc="Data access platform", is_admin=True)
    key = user.issue_key()
    print("ADMIN KEY: {}".format(key))
    with LOCAL_CONN.new_session() as session:
        session.add(user)


def create_db_user(user, pswd):
    """Creates a user in MySQL."""
    conn = LOCAL_CONN.connect()
    conn.execute("CREATE USER '{}'@'localhost' IDENTIFIED BY '{}'".format(user, pswd))
    conn.execute("CREATE USER '{}'@'%' IDENTIFIED BY '{}'".format(user, pswd))
    conn.close()


class Logger(object):
    """Middleware class for request/response logging."""
    def process_request(self, req, resp):
        """Logs incoming requests.

        Args:
            see falcon documentation.
        """
        rid = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8)) # a random request id
        req.context['_rid'] = rid
        content = req.context['doc'] if 'doc' in req.context else None
        log.info("**REQUEST**  [{}] from: [{}], route: {}, content: {}".format(rid, req.remote_addr, req.path, content))

    def process_response(self, req, resp, resource, req_succeeded):
        """Logs responses.

        Args:
            see falcon documentation.
        """
        # `resp.body` is not translated from `context` yet if no exception is raised.
        content = resp.context['result'] if req_succeeded else resp.body
        log.info("**RESPONSE** [{}] content: {}, succeeded: {}".format(
            req.context['_rid'], content, req_succeeded))


class RequireAuth(object):
    """Middleware class for key validation.

    Attributes:
        exempts (list): suffixes of paths which do not require authentication.
    """

    exempts = []

    def process_resource(self, req, resp, resource, params):
        """Validates the key and insert the user into the request.

        Args:
            see falcon documentation.
        """
        for item in RequireAuth.exempts:
            if req.path.endswith(item):
                return

        key = req.auth
        with LOCAL_CONN.new_session() as session:
            user = User.auth(session, key)
        if user:
            req.context['user'] = user
        else:
            raise exceptions.HTTPForbiddenError("Invalid key")


def _match_route(path, root):
    root = '/' + root
    return path.startswith(root)


class AdminCheck(object):
    """Middleware class for Admin check.

    Attributes:
        admin (list): suffixes of paths which require admin privilege.
    """

    admin = ['register', 'privilege', 'key']

    def process_resource(self, req, resp, resource, params):
        """Validates the token and insert the payload into the request.

        Args:
            see falcon documentation.
        """
        is_admin = req.context['user']['is_admin']
        require_admin = False

        for item in AdminCheck.admin:
            if _match_route(req.path, item):
                require_admin = True
                break

        if require_admin and not is_admin:
            raise exceptions.HTTPForbiddenError("Insufficient privilege")
        if not require_admin and is_admin:
            raise exceptions.HTTPForbiddenError("Access forbidden for admin account")


class RequireJSON(object):
    """Deny requests without 'Content-type:application/json' header."""
    def process_request(self, req, resp):
        if req.method in ('POST', 'PUT'):
            if not req.content_type or 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.')


class JSONTranslator(object):
    """Serialize and Deserialize json in response and request.
    
    Deserialize json content and insert into req.context['doc'];
    Serialize object in resp.context['result'] into the response.
    """
    #@do_cprofile
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
    elif code == 1142:
        raise exceptions.HTTPForbiddenError("Insufficent privileges")
    else:
        description = ('Unspecified error')
        raise exceptions.HTTPForbiddenError(description)

def handle_sql_exception(ex, req, resp, params):
    if (type(ex) == exc.NoSuchTableError):
        log.warn("table not exist: {}".format(params))
        raise exceptions.HTTPBadRequestError("Table not exist")
    else:
        log.exception(ex)
        raise exceptions.HTTPBadRequestError("Unspecified error")
