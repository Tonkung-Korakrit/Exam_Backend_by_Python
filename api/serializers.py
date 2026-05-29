from rest_framework import serializers
from .models import Product, Profile
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