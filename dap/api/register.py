import falcon

import dap.utils

from dap import exceptions
from dap.user import User
from dap.db import LOCAL_CONN


class Register(object):
    def on_post(self, req, resp):
        user = req.context['user']
        if not user or not user['is_admin']:
            raise exceptions.HTTPForbiddenError("Invalid admin key")
        data = req.context['doc']

        required = ['app', 'description']
        for field in required:
            if field not in data.keys():
                raise exceptions.HTTPMissingParamError(field)

        user = User.new(app=data['app'], desc=data['desc'])
        with LOCAL_CONN.new_session() as session:
            utils.create_db_user(user.user, user.pswd)
            # TODO: success check
            session.add(user)

        resp.status = falcon.HTTP_201

