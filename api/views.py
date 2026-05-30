from django.shortcuts import render, get_object_or_404

from rest_framework import viewsets, permissions, generics, status
from .models import Product, Cart, CartItem, Product, Order, OrderItem
from .serializers import RegisterSerializer, ProductSerializer, UserProfileSerializer, ProductListSerializer, ProductDetailSerializer, CartSerializer, OrderSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .permissions import IsSellerOwnerOrReadOnly, IsBuyer
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction # สำคัญมาก ตอน Checkout

from rest_framework.permissions import IsAuthenticated

# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user จะเก็บข้อมูลของคนที่ล็อกอินอยู่โดยอัตโนมัติ (อ่านจาก Token)
        user = request.user
        
        # เอา user ไปแปลงเป็น JSON ผ่าน Serializer
        serializer = UserProfileSerializer(user)
        
        # ส่งข้อมูลกลับไป
        return Response(serializer.data)

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

class MyProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ดึงมาเฉพาะสินค้าที่ฟิลด์ seller ตรงกับคนที่กำลังล็อกอิน (request.user)
        return Product.objects.filter(seller=self.request.user)

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

    def delete(self, request):
        # 1. ดึงตะกร้าของ user คนนี้
        cart, created = Cart.objects.get_or_create(buyer=request.user)
        
        # 2. รับ product_id ที่ต้องการลบจาก request
        product_id = request.data.get('product_id')
        
        # 3. ค้นหาสินค้าในตะกร้า
        cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
        
        if not cart_item:
            return Response({"error": "ไม่พบสินค้าชิ้นนี้ในตะกร้า"}, status=status.HTTP_404_NOT_FOUND)
        
        # 4. ลบสินค้าชิ้นนั้นออกจากตะกร้า
        cart_item.delete()
        
        return Response({"message": "ลบสินค้าออกจากตะกร้าเรียบร้อยแล้ว"}, status=status.HTTP_200_OK)

class CartItemDetailView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # ล็อกไว้ว่าต้องลบได้เฉพาะของตัวเองเท่านั้น
        return CartItem.objects.filter(cart__buyer=self.request.user)

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
    
class OrderHistoryListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ดึงเฉพาะรายการสั่งซื้อของคนที่ล็อกอิน และเรียงจากล่าสุดไปเก่าสุด
        return Order.objects.filter(buyer=self.request.user).order_by('-created_at')