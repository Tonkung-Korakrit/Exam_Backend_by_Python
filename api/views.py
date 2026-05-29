from django.shortcuts import render, get_object_or_404

from rest_framework import viewsets, permissions, generics, status
from .models import Product, Cart, CartItem, Product, Order, OrderItem
from .serializers import RegisterSerializer, ProductSerializer, ProductListSerializer, ProductDetailSerializer, CartSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .permissions import IsSellerOwnerOrReadOnly, IsBuyer
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction # สำคัญมาก ตอน Checkout

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

# สำหรับจัดการตะกร้า
class CartView(APIView):
    permission_classes = [IsBuyer]

    def get(self, request):
        # ดึงตะกร้าของ Buyer
        cart, created = Cart.objects.get_or_create(buyer=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        cart, created = Cart.objects.get_or_create(buyer=request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)

        # เช็คสต็อกก่อนว่ามีพอไหม
        if quantity > product.available_quantity:
            return Response({"error": "สินค้ามีไม่เพียงพอ"}, status=status.HTTP_400_BAD_REQUEST)

        # ใส่ของลงตะกร้า (ถ้ามีอยู่แล้ว ให้บวกจำนวนเพิ่ม)
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not item_created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
            
        # เช็คสต็อกซ้ำอีกรอบหลังบวกเพิ่ม
        if cart_item.quantity > product.available_quantity:
             return Response({"error": "จำนวนสินค้าในตะกร้าเกินสต็อกที่มี"}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.save()
        return Response({"message": "เพิ่มสินค้าลงตะกร้าเรียบร้อย"}, status=status.HTTP_200_OK)

# กดจ่ายเงิน และตัดสต็อก
class PaymentView(APIView):
    permission_classes = [IsBuyer]

    # @transaction.atomic ถ้าระหว่างตัดสต็อกเกิด Error มันจะ Rollback คืนค่าทุกอย่างให้ จำนวนสินค้าจะไม่ผิดเพี้ยน
    @transaction.atomic 
    def post(self, request):
        cart = get_object_or_404(Cart, buyer=request.user)
        
        if not cart.items.exists():
            return Response({"error": "ไม่มีสินค้าในตะกร้า"}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(buyer=request.user, total_price=0)
        total_price = 0

        # วนลูปสินค้าในตะกร้า เพื่อย้ายไปลง OrderItem และตัดสต็อก Product
        for item in cart.items.all():
            if item.quantity > item.product.available_quantity:
                raise Exception(f"ขออภัย สินค้า '{item.product.title}' หมดหรือมีไม่พอ")
            
            # ตัดสต็อก!
            item.product.available_quantity -= item.quantity
            item.product.save()

            # บันทึกประวัติลง OrderItem
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=item.product.unit_price
            )
            total_price += (item.quantity * item.product.unit_price)

        # อัปเดตราคารวมของบิล
        order.total_price = total_price
        order.save()

        # ล้างตะกร้าให้ว่างเปล่า
        cart.items.all().delete()

        return Response({
            "message": "สั่งซื้อสำเร็จ!", 
            "order_id": order.id,
            "total_price": total_price
        }, status=status.HTTP_201_CREATED)