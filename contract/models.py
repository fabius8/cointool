from django.db import models
import django_filters

# Create your models here.
class Tradepair(models.Model):
    symbol = models.CharField(max_length=100, verbose_name="交易对")
    futureprice = models.FloatField(verbose_name="合约价格")
    spotprice = models.FloatField(verbose_name="现货价格")
    exchange = models.CharField(max_length=100, verbose_name="交易所")
    LastRate = models.FloatField(verbose_name="上期资费(%)")
    fundRate = models.FloatField(verbose_name="本期资费(%)")
    sellSpread = models.FloatField(verbose_name="合约做空盈亏(%)")
    buySpread = models.FloatField(verbose_name="合约做多盈亏(%)")

class TradepairFilter(django_filters.FilterSet):
    symbol = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Tradepair
        fields = ['symbol']
