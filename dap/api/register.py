import falcon

from dap import exceptions
from dap.user import User
from dap.utils import basic_backend
from dap.db import LOCAL_CONN


class Register(object):
    auth = {
        'backend': basic_backend
    }

    def on_post(self, req, resp):
        user = req.context['user']
        if not user or not user['is_admin']:
            raise falcon.HTTPForbidden("Admin login failed", "Invalid username or password")
        data = req.context['doc']

        required = ['name', 'password', 'db_addr', 'db_name']
        for field in required:
            if field not in data.keys():
                raise exceptions.HTTPMissingParamError(field)

        user = User.new(name=data['name'], pswd=data['password'], db_addr=data['db_addr'], db_port=data['db_port'], db_pswd=data['db_pswd'], db_name=data['db_name'])
        with LOCAL_CONN.new_session() as session:
            session.add(user)

        resp.status = falcon.HTTP_201

