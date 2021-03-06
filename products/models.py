"""
Product models used in database and admin
"""
from django.db import models
from artists.models import Artist


class Product(models.Model):
    """
    A class to contain all products
    """
    sku = models.CharField(max_length=254, null=True, blank=True)
    base_price = models.DecimalField(max_digits=6, decimal_places=2)
    rating = models.DecimalField(max_digits=6, decimal_places=1,
                                 null=True, blank=True)
    image_url = models.URLField(max_length=1024, null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE,
                               related_name="products")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sku
