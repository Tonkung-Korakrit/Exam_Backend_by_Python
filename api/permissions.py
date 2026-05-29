from rest_framework import permissions

class IsSellerOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # ถ้า GET, HEAD, OPTIONS ผ่านได้
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # ถ้า POST / PUT / PATCH ต้อง Login และต้องมี Role SELLER
        is_authenticated = bool(request.user and request.user.is_authenticated)
        is_seller = hasattr(request.user, 'profile') and request.user.profile.role == 'SELLER'
        
        return is_authenticated and is_seller

    # ตรวจสิทธิ์ตอนจะจัดการสินค้าแบบเจาะจง (PUT, PATCH, DELETE)
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # ถ้า POST / PUT / PATCH / DELETE สินค้านั้น ชื่อผู้ขายในสินค้า ต้องตรงกับคนที่ล็อกอินอยู่เท่านั้น
        return obj.seller == request.user