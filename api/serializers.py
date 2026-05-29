from rest_framework import serializers
from .models import Product, Profile, Cart, CartItem
from django.contrib.auth.models import User

class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=Profile.Role.choices, default=Profile.Role.BUYER)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role']

    def create(self, validated_data):
        role = validated_data.pop('role') # ดึง role ออกมาก่อน
        
        # ใช้ create_user เพื่อเข้ารหัส Password อัตโนมัติ
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        
        Profile.objects.create(user=user, role=role)
        
        return user

class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.username', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'seller', 'seller_name', 'title', 'description', 'image', 'unit_price', 'available_quantity', 'created_at']
        # ป้องกันไม่ให้คนอื่นมาแก้ ID คนขายได้
        read_only_fields = ['seller']

class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'image', 'unit_price', 'available_quantity']

class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    unit_price = serializers.DecimalField(source='product.unit_price', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_title', 'unit_price', 'quantity', 'subtotal']

    def get_subtotal(self, obj):
        return obj.quantity * obj.product.unit_price

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'buyer', 'items', 'total_price']

    def get_total_price(self, obj):
        return sum(item.quantity * item.product.unit_price for item in obj.items.all())