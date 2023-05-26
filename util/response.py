from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND


class StatusResponse(Response):
    def __init__(self, message: str, status: int = HTTP_200_OK):
        super().__init__({"code": status, "message": message})


class DoesNotExistResponse(StatusResponse):
    def __init__(self, cls: str):
        super().__init__(message=f"{cls} does not exist", status=HTTP_404_NOT_FOUND)
