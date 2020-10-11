from django.db import models

# Create your models here.
class Tradepair(models.Model):
    symbol = models.CharField(max_length=100, verbose_name="交易对")
    futureprice = models.FloatField(verbose_name="合约价格")
    spotprice = models.FloatField(verbose_name="现货价格")
    exchange = models.CharField(max_length=100, verbose_name="交易所")
    fundRate = models.FloatField(verbose_name="资费(%)")
    sellSpread = models.FloatField(verbose_name="合约做空盈亏(%)")
    buySpread = models.FloatField(verbose_name="合约做多盈亏(%)")
