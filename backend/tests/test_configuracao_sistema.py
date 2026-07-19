"""Testes da configuração global do sistema (estilo de ícones do menu)."""

import pytest
from django.urls import reverse

from apps.audit.models import LogAuditoria
from apps.common.models import ConfiguracaoSistema

pytestmark = pytest.mark.django_db


def test_get_retorna_padrao_por_default(cliente_autenticado_usuario):
    url = reverse("configuracao-sistema")
    response = cliente_autenticado_usuario.get(url)
    assert response.status_code == 200
    assert response.data["estilo_icone"] == "padrao"


def test_get_exige_autenticacao(api_client):
    url = reverse("configuracao-sistema")
    response = api_client.get(url)
    assert response.status_code == 401


def test_usuario_comum_nao_pode_alterar(cliente_autenticado_usuario):
    url = reverse("configuracao-sistema")
    response = cliente_autenticado_usuario.patch(url, {"estilo_icone": "preenchido"}, format="json")
    assert response.status_code == 403
    assert ConfiguracaoSistema.obter().estilo_icone == "padrao"


def test_admin_pode_alterar_e_gera_auditoria(cliente_autenticado_admin):
    url = reverse("configuracao-sistema")
    response = cliente_autenticado_admin.patch(url, {"estilo_icone": "contornado"}, format="json")
    assert response.status_code == 200
    assert response.data["estilo_icone"] == "contornado"
    assert ConfiguracaoSistema.obter().estilo_icone == "contornado"
    assert LogAuditoria.objects.filter(entidade="ConfiguracaoSistema").exists()


def test_alterar_para_o_mesmo_valor_nao_duplica_auditoria(cliente_autenticado_admin):
    url = reverse("configuracao-sistema")
    cliente_autenticado_admin.patch(url, {"estilo_icone": "preenchido"}, format="json")
    total_apos_primeira = LogAuditoria.objects.filter(entidade="ConfiguracaoSistema").count()
    cliente_autenticado_admin.patch(url, {"estilo_icone": "preenchido"}, format="json")
    total_apos_segunda = LogAuditoria.objects.filter(entidade="ConfiguracaoSistema").count()
    assert total_apos_primeira == 1
    assert total_apos_segunda == 1


def test_valor_invalido_e_rejeitado(cliente_autenticado_admin):
    url = reverse("configuracao-sistema")
    response = cliente_autenticado_admin.patch(url, {"estilo_icone": "neon"}, format="json")
    assert response.status_code == 400
