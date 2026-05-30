from django.test import TestCase

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import Profile, Product, Cart, CartItem
from django.core.files.uploadedfile import SimpleUploadedFile

# Create your tests here.
class ProductAccessTests(APITestCase):
    def setUp(self):  
        # สร้างบัญชีผู้ขาย
        self.seller = User.objects.create_user(username='seller01', password='password')
        Profile.objects.create(user=self.seller, role='SELLER')
        self.seller.profile.save()

        # สร้างบัญชีผู้ซื้อ
        self.buyer = User.objects.create_user(username='buyer01', password='password')
        Profile.objects.create(user=self.buyer, role='BUYER')
        self.buyer.profile.save()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        dummy_image = SimpleUploadedFile('test.gif', small_gif, content_type='image/gif')

        # ข้อมูลสินค้าจำลอง
        self.product_data = {
            "title": "คีย์บอร์ด Test",
            "description": "ทดสอบๆ",
            "unit_price": "1500.00",
            "available_quantity": 10,
            "image": dummy_image
        }

    def test_seller_can_create_product(self):
        # บังคับล็อกอินด้วยบัญชี Seller
        self.client.force_authenticate(user=self.seller)
        
        # ยิง API สร้างสินค้า
        response = self.client.post('/api/products/', self.product_data, format='multipart')
        
        # Debug Errors
        # print("API ERROR REASON:", response.data)

        # ตรวจสอบว่าต้องได้สถานะ 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # ตรวจสอบว่าสินค้าถูกสร้างใน Database จริงๆ
        self.assertEqual(Product.objects.count(), 1)

    def test_buyer_cannot_create_product(self):
        # บังคับล็อกอินด้วยบัญชี Buyer
        self.client.force_authenticate(user=self.buyer)
        
        # ยิง API สร้างสินค้า
        response = self.client.post('/api/products/', self.product_data)
        
        # ตรวจสอบว่าต้องโดนเตะออก (403 Forbidden) เพราะไม่มีสิทธิ์
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # ตรวจสอบว่าต้องไม่มีสินค้าถูกสร้างขึ้น
        self.assertEqual(Product.objects.count(), 0)


class PaymentInventoryTests(APITestCase):
    def setUp(self):
        # สร้างบัญชี Buyer
        self.buyer = User.objects.create_user(username='buyer02', password='password')
        Profile.objects.create(user=self.buyer, role='BUYER')
        self.buyer.profile.save()

        # สร้างสินค้า มีสต็อก 10 ชิ้น
        self.product = Product.objects.create(
            seller=self.buyer, # สมมติให้ใครเป็นคนขายก็ได้ในเคสนี้
            title="เมาส์",
            unit_price=500.00,
            available_quantity=10
        )

    def test_payment_deducts_inventory_correctly(self):
        # บังคับล็อกอิน
        self.client.force_authenticate(user=self.buyer)
        
        # จำลองการสร้างตะกร้า และใส่ของลงไป 2 ชิ้น
        cart = Cart.objects.create(buyer=self.buyer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        # ยิง API สั่งจ่ายเงิน
        response = self.client.post('/api/cart/payment/')

        # ตรวจสอบผลลัพธ์ว่าสำเร็จ
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 🌟 จุดสำคัญ: ดึงข้อมูลสินค้าจาก Database ขึ้นมาใหม่เพื่อเช็คสต็อก
        self.product.refresh_from_db()
        
        # สต็อกต้องเหลือ 8 (10 - 2)
        self.assertEqual(self.product.available_quantity, 8)
        
        # ตะกร้าต้องถูกล้างของออกหมด
        self.assertEqual(cart.items.count(), 0)