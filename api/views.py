from django.shortcuts import render

from rest_framework import viewsets, permissions, generics
from .models import Product
from .serializers import RegisterSerializer, ProductSerializer, ProductListSerializer, ProductDetailSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .permissions import IsSellerOwnerOrReadOnly
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter

# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    permission_classes = [IsSellerOwnerOrReadOnly] 

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_class = ProductFilter           
    search_fields = ['title', 'description', 'seller__username']   
    ordering_fields = ['unit_price', 'created_at']

    def get_serializer_class(self):
        # ถ้าเป็นการเรียกดูหน้ารวม (GET /api/products/)
        if self.action == 'list':
            return ProductListSerializer
        
        # ถ้าเป็นการกระทำอื่นๆ (GET แบบระบุ ID, POST, PUT, PATCH) ให้ใช้แบบจัดเต็ม
        return ProductDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)