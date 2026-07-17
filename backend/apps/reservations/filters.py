import django_filters

from .models import Reserva


class ReservaFilter(django_filters.FilterSet):
    data_de = django_filters.DateTimeFilter(field_name="data_inicio", lookup_expr="gte")
    data_ate = django_filters.DateTimeFilter(field_name="data_fim", lookup_expr="lte")

    class Meta:
        model = Reserva
        fields = ["ambiente", "solicitante", "status", "data_de", "data_ate"]
