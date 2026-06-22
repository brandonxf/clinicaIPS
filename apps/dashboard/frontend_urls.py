from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.authentication.roles import RoleRequiredMixin

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'
    login_url = '/login/'

class LoginPageView(TemplateView):
    template_name = 'auth/login.html'

class EtlView(RoleRequiredMixin, TemplateView):
    template_name = 'etl/index.html'
    allowed_roles = ['analista', 'administrador']

class MlView(RoleRequiredMixin, TemplateView):
    template_name = 'ml/index.html'
    allowed_roles = ['analista', 'administrador']

class PacientesView(RoleRequiredMixin, TemplateView):
    template_name = 'dashboard/pacientes.html'
    allowed_roles = ['medico', 'administrador', 'analista']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_rol'] = self.request.user.rol if self.request.user.is_authenticated else ''
        return context

class UsuariosView(RoleRequiredMixin, TemplateView):
    template_name = 'auth/usuarios.html'
    allowed_roles = ['administrador']

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginPageView.as_view(), name='login_page'),
    path('etl/', EtlView.as_view(), name='etl_page'),
    path('ml/', MlView.as_view(), name='ml_page'),
    path('pacientes/', PacientesView.as_view(), name='pacientes_page'),
    path('usuarios/', UsuariosView.as_view(), name='usuarios_page'),
]
