import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    # กรองราคาขั้นต่ำ
    min_price = django_filters.NumberFilter(field_name="unit_price", lookup_expr='gte')
    # กรองราคาสูงสุด
    max_price = django_filters.NumberFilter(field_name="unit_price", lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['min_price', 'max_price']