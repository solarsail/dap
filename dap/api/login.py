import falcon

from dap.utils import jwt_backend, basic_backend



class Login(object):
    auth = {
        'backend': basic_backend
    }

    def on_get(self, req, resp):
        user = req.context['user']
        token = jwt_backend.get_auth_token(user)
        resp.context['result'] = { 'token': token }
        resp.status = falcon.HTTP_200

