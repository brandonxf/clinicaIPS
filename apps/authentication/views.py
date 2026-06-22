from django.contrib.auth import login as django_login
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema
from .serializers import RegistroSerializer, UsuarioSerializer, CustomTokenSerializer


@extend_schema(
    tags=['auth'],
    summary='Iniciar sesion con JWT',
    description='Autentica un usuario y retorna tokens de acceso y refresco.',
    request=CustomTokenSerializer,
    responses={200: {'type': 'object', 'properties': {
        'access': {'type': 'string'}, 'refresh': {'type': 'string'},
        'username': {'type': 'string'}, 'rol': {'type': 'string'}
    }}},
)
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        django_login(request, serializer.user)
        response = super().post(request, *args, **kwargs)
        user = serializer.user
        response.data['username'] = user.username
        response.data['rol'] = user.rol
        response.data['rol_display'] = user.get_rol_display()
        response.data['nombres'] = user.get_full_name() or user.username
        response.data['email'] = user.email
        return response

    def get_serializer_context(self):
        return {'request': self.request}


@extend_schema(
    tags=['auth'],
    summary='Registrar nuevo usuario',
    description='Crea una cuenta con username, email, password y rol.',
    request=RegistroSerializer,
    responses={201: UsuarioSerializer},
)
@api_view(['POST'])
@permission_classes([AllowAny])
def registro(request):
    serializer = RegistroSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UsuarioSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['auth'],
    summary='Obtener perfil del usuario autenticado',
    description='Retorna los datos del usuario actualmente autenticado.',
    responses={200: UsuarioSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil(request):
    return Response(UsuarioSerializer(request.user).data)
