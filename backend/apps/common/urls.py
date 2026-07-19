from django.urls import path

from .views import ConfiguracaoSistemaView

urlpatterns = [
    path("configuracao-sistema/", ConfiguracaoSistemaView.as_view(), name="configuracao-sistema"),
]
