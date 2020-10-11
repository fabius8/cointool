from django.shortcuts import render
from django_tables2 import RequestConfig

# Create your views here.
from .models import Tradepair
from .tables import PairTable

def pair(request):
    table = PairTable(Tradepair.objects.all())
    RequestConfig(request).configure(table)
    return render(request, 'contract/pair.html', {
        'table': table
    })
