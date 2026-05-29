from django.shortcuts import render

from rest_framework import viewsets, permissions, generics
from .models import Product
from .serializers import RegisterSerializer, ProductSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .permissions import IsSellerOwnerOrReadOnly

# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    permission_classes = [IsSellerOwnerOrReadOnly] 

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)