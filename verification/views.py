import uuid

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_403_FORBIDDEN

from util.response import StatusResponse
from verification.models import Verification
from verification.serializers import VerificationRequestSerializer, VerificationConfirmSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def verification_request(request):
    serializer = VerificationRequestSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({"verification": serializer.instance.id})


@api_view(["POST"])
@permission_classes([AllowAny])
def verification_confirm(request):
    serializer = VerificationConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    fail_response = StatusResponse("The combination of verification ID and token is not correct", HTTP_403_FORBIDDEN)

    try:
        verification = Verification.objects.get(id=serializer.validated_data["verification"])
    except Verification.DoesNotExist:
        return fail_response

    if verification.token != serializer.validated_data["token"]:
        return fail_response

    if verification.secret is not None:
        return fail_response

    verification.secret = uuid.uuid4()
    verification.save()
    return Response({"secret": verification.secret})
