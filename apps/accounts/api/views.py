from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import MeSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="get_current_user",
        summary="Get current authenticated user",
        responses={200: MeSerializer},
        tags=["auth"],
    )
    def get(self, request: Request) -> Response:
        return Response(MeSerializer(request.user).data)
