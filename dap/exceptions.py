import falcon

from sqlalchemy import exc


class DAPHTTPError(falcon.HTTPError):
    """Base class for custom falcon exceptions."""
    def __init__(self, status, msg):
        super(DAPHTTPError, self).__init__(status)
        self.message = msg

    def to_dict(self, obj_type=dict):
        obj = obj_type()
        obj['result'] = 'err'
        obj['description'] = self.message
        return obj


class HTTPServerError(DAPHTTPError):
    """Unable to service due to backend server errors."""
    def __init__(self, msg):
        super(HTTPServerError, self).__init__(falcon.HTTP_500, msg)


class HTTPBadRequestError(DAPHTTPError):
    """Request not processable."""
    def __init__(self, msg):
        super(HTTPBadRequestError, self).__init__(falcon.HTTP_400, msg)


class HTTPForbiddenError(DAPHTTPError):
    def __init__(self, msg):
        super(HTTPForbiddenError, self).__init__(falcon.HTTP_403, msg)


class HTTPMissingParamError(DAPHTTPError):
    def __init__(self, msg):
        super(HTTPMissingParamError, self).__init__(falcon.HTTP_400, "Missing parameter: {}".format(msg))

