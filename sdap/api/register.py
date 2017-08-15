import logging
import falcon

from sdap import exceptions, utils
from sdap.user import User
from sdap.db import LOCAL_CONN


log = logging.getLogger(__name__)

class Register(object):
    def on_post(self, req, resp):
        data = req.context['doc']

        required = ['app', 'description']
        for field in required:
            if field not in data.keys():
                raise exceptions.HTTPMissingParamError(field)

        user = User.new(app=data['app'], desc=data['description'])

        # exceptions will be handled by falcon
        utils.create_db_user(user.user, user.pswd)
        with LOCAL_CONN.new_session() as session:
            session.add(user)

        resp.context['result'] = { 'result': 'ok' }
        resp.status = falcon.HTTP_201

