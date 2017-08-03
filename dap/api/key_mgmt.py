import logging
import falcon

from dap import exceptions, utils
from dap.user import User
from dap.db import LOCAL_CONN


log = logging.getLogger(__name__)

class KeyManagement(object):
    def on_post(self, req, resp, app):

        def get_key(user):
            return user.issue_key()

        with LOCAL_CONN.new_session() as session:
            key = User.modify_user(session, app, get_key)

        resp.context['result'] = { 'result': 'ok', 'key': key }
        resp.status = falcon.HTTP_201

    def on_delete(self, req, resp, app):

        def erase_key(user):
            user.key = ''

        with LOCAL_CONN.new_session() as session:
            User.modify_user(session, app, erase_key)

        resp.context['result'] = { 'result': 'ok' }
        resp.status = falcon.HTTP_200

