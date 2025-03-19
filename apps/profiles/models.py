from django.db import models

from apps.accounts.models   import User
from apps.common.models     import BaseModel
from apps.common.utils      import generate_unique_code
from apps.shop.models       import Product


class ShippingAddress(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shipping_addresses"
    )
    full_name = models.CharField(max_length=1000)
    email = models.EmailField()
    phone = models.CharField(max_length=20, null=True)
    address = models.CharField(max_length=1000, null=True)
    city = models.CharField(max_length=200, null=True)
    country = models.CharField(max_length=200, null=True)
    zipcode = models.CharField(max_length=10, null=True)

    def __str__(self):
        return f"{self.full_name}'s shipping details"
    


DELIVERY_STATUS_CHOICES = (
    ('PENDING', 'PENDING'),
    ('PACKING', 'PACKING'),
    ('SHIPPING', 'SHIPPING'),
    ('ARRIVING', 'ARRIVING'),
    ('SUCCESS', 'SUCCESS'),
)

PAYMENT_STATUS_CHOICES = (
    ('PENDING', 'PENDING'),
    ('PROCESSING', 'PROCESSING'),
    ('SUCCESSFULL', 'SUCCESSFULL'),
    ('CANCELED', 'CANCELED'),
    ('FAILED', 'FAILED'),
)

class Order(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')

    tx_ref = models.CharField(max_length=100, blank=True, unique=True)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')

    date_delivered = models.DateTimeField(null=True, blank=True)

    full_name = models.CharField(max_length=1000, null=True)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=20, null=True)
    address = models.CharField(max_length=1000, null=True)
    city = models.CharField(max_length=200, null=True)
    country = models.CharField(max_length=100, null=True)
    zipcode = models.CharField(max_length=10, null=True)

    def __str__(self):
        return f"{self.user.full_name}'s order"

    def save(self, *args, **kwargs) -> None:
        if self._state.adding:
            self.tx_ref = generate_unique_code(Order, "tx_ref")
        super().save(*args, **kwargs)

    @property
    def get_cart_subtotal(self):
        orderitems = self.orderitems.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_total(self):
        total = self.get_cart_subtotal
        return total


class OrderItem(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='orderitems', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def get_total(self):
        return self.product.price_current * self.quantity

    def __str__(self):
        return str(self.product.name)

    class Meta:
        ordering = ["-created_at"]
        