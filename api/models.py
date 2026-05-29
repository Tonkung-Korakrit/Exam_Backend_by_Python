from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.
# 1. ตาราง Profile User ที่แบ่งตาม role
class Profile(models.Model):
    class Role(models.TextChoices):
        BUYER = 'BUYER', 'Buyer'
        SELLER = 'SELLER', 'Seller'

    # เชื่อมโยงกับตาราง User แบบ one-to-one
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(
        max_length=10, 
        choices=Role.choices, 
        default=Role.BUYER
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"


# 2. ตาราง Product
class Product(models.Model):
    # ผู้ขาย: ดึงจาก User ที่มี Profile Role เป็น SELLER เท่านั้น
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)
    
    # อัปโหลดไฟล์รูปภาพ (images/products/.)
    image = models.ImageField(upload_to='products/')
    
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    available_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    # Validation ป้องกันไม่ให้ผู้ซื้อมาลงขายสินค้า
    def clean(self):
        if hasattr(self.seller, 'profile') and self.seller.profile.role != Profile.Role.SELLER:
            raise ValidationError("เฉพาะผู้ใช้งานที่มีสิทธิ์เป็น 'ผู้ขาย' เท่านั้นที่สามารถลงสินค้าได้")


# 3. ตาราง Shopping Cart
class Cart(models.Model):
    buyer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ตะกร้าของ {self.buyer.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.title} ในตะกร้า"
    
    def clean(self):
        if self.quantity > self.product.available_quantity:
            raise ValidationError(f"สินค้า {self.product.title} มีจำนวนไม่พอ (เหลือ {self.product.available_quantity} ชิ้น)")


# 4. ตาราง Orders & Purchase
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"คำสั่งซื้อ #{self.id} โดย {self.buyer.username}"


# ตาราง OrderItem
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.title if self.product else 'สินค้าถูกลบ'} (คำสั่งซื้อ #{self.order.id})"