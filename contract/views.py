from django.shortcuts import render
from django_tables2 import RequestConfig
from django.db.models import Q

# Create your views here.
from .models import Tradepair
from .models import TradepairFilter
from .tables import PairTable

def pair(request):
    filter = TradepairFilter(request.GET, queryset=Tradepair.objects.all())
    table0 = PairTable(Tradepair.objects.filter(Q(sellSpread__gte=1)|Q(buySpread__gte=1)))
    table1 = PairTable(Tradepair.objects.filter(Q(exchange="binance")&(Q(fundRate__gt=0.01)|Q(fundRate__lte=-0.05)|Q(buySpread__gte=0.35)|Q(sellSpread__gte=0.35))), prefix="1-")
    table2 = PairTable(Tradepair.objects.filter(Q(exchange="okex")&(Q(fundRate__gte=0.1)|Q(fundRate__lte=-0.1)|Q(buySpread__gte=0.5)|Q(sellSpread__gte=0.5))), prefix="2-")
    table3 = PairTable(Tradepair.objects.filter(Q(exchange="huobi")&(Q(fundRate__gte=0.1)|Q(fundRate__lte=-0.1)|Q(buySpread__gte=0.5)|Q(sellSpread__gte=0.5))), prefix="3-")
    RequestConfig(request, paginate={"per_page": 20}).configure(table0)
    RequestConfig(request, paginate={"per_page": 10}).configure(table1)
    RequestConfig(request, paginate={"per_page": 10}).configure(table2)
    RequestConfig(request, paginate={"per_page": 10}).configure(table3)
    return render(request, 'contract/pair.html', {
        'table0': table0,
        'table1': table1,
        'table2': table2,
        'table3': table3,
        'filter': filter,
    })
