from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, UserProfileView, ProductViewSet, MyProductListView, CartView, PaymentView, OrderHistoryListView, CartItemDetailView

from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view(), name='register'),
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),

    # Product
    path('products/me/', MyProductListView.as_view(), name='my-products'),
    
    # Cart & Checkout
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/payment/', PaymentView.as_view(), name='checkout'),
    path('cart/<int:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),
    
    # Order
    path('orders/history/', OrderHistoryListView.as_view(), name='order-history'),

    # อื่นๆ จาก Router
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)