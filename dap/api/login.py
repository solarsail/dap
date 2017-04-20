import falcon

from dap.utils import jwt_backend, basic_backend



class Login(object):
    auth = {
        'backend': basic_backend
    }

    def on_get(self, req, resp):
        user = req.context['user']
        # Cannot use user object directly as token payload,
        # since the object has to be bound to a DB session.
        token = jwt_backend.get_auth_token(user)
        resp.context['result'] = { 'token': token }
        resp.status = falcon.HTTP_200
