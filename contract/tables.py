import django_tables2 as tables
from .models import Tradepair
from .models import TradepairFilter
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

class PairTable(tables.Table):
    class Meta:
        model = Tradepair
        template_name = 'django_tables2/bootstrap.html'

class FilteredPairListView(SingleTableMixin, FilterView):
    table_class = PairTable
    model = Tradepair
    template_name = 'django_tables2/bootstrap.html'
    filterset_class = TradepairFilter
