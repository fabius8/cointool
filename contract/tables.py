import django_tables2 as tables
from .models import Tradepair

class PairTable(tables.Table):
    class Meta:
        model = Tradepair
        template_name = 'django_tables2/bootstrap.html'
