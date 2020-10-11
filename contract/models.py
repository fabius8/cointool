from django.db import models

# Create your models here.
class Tradepair(models.Model):
    symbol = models.CharField(max_length=100, verbose_name="交易对")
    fundRate = models.FloatField(verbose_name="资费")
    buySpread = models.FloatField(verbose_name="买入价差")
    sellSpread = models.FloatField(verbose_name="卖出价差")
