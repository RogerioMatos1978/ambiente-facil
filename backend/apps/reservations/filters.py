import django_filters

from .models import Reserva


class ReservaFilter(django_filters.FilterSet):
    """
    data_de/data_ate definem uma janela de tempo e retornam reservas que se
    sobrepõem a ela (não só as que começam e terminam inteiramente dentro da
    janela). Isso é o que faz sentido para calendário, relatórios e
    exportações: uma reserva que começou antes da janela mas ainda está em
    andamento quando ela começa (ou que termina depois da janela) continua
    sendo "uma reserva desse período" e precisa aparecer.
    """

    data_de = django_filters.DateTimeFilter(method="filtrar_data_de")
    data_ate = django_filters.DateTimeFilter(method="filtrar_data_ate")

    class Meta:
        model = Reserva
        fields = ["ambiente", "solicitante", "status", "data_de", "data_ate"]

    def filtrar_data_de(self, queryset, name, value):
        return queryset.filter(data_fim__gt=value)

    def filtrar_data_ate(self, queryset, name, value):
        return queryset.filter(data_inicio__lt=value)
