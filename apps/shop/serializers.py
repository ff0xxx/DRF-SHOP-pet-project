from rest_framework         import serializers
from drf_spectacular.utils  import extend_schema_field

from apps.sellers.serializers   import SellerSerializer
from apps.profiles.serializers  import ShippingAddressSerializer, ProfileSerializer
from apps.shop.models           import RATING_CHOICES, Review


class CategorySerializer(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.SlugField(read_only=True)
    image = serializers.ImageField()


class SellerShopSerializer(serializers.Serializer):
    name = serializers.CharField(source="business_name")
    slug = serializers.CharField()
    avatar = serializers.CharField(source="user.avatar")


class ProductSerializer(serializers.Serializer):
    seller = SellerShopSerializer()
    name = serializers.CharField()
    rating = serializers.SerializerMethodField()
    slug = serializers.SlugField()
    desc = serializers.CharField()
    price_old = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = CategorySerializer()
    in_stock = serializers.IntegerField()
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    image3 = serializers.ImageField(required=False)

    def get_rating(self, obj):
        reviews = Review.objects.filter(product__slug=obj.slug).only('rating')
        count = reviews.count()
        if count == 0:
            return 0
        rating_sum = sum(review.rating for review in reviews)
        return round(rating_sum / count, 1)


class CreateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    desc = serializers.CharField()
    price_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    category_slug = serializers.CharField()
    in_stock = serializers.IntegerField()
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    image3 = serializers.ImageField(required=False)


class OrderItemProductSerializer(serializers.Serializer):
    seller = SellerSerializer()
    name = serializers.CharField()
    slug = serializers.SlugField()
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, source='price_current'
    )


class OrderItemSerializer(serializers.Serializer):
    product = OrderItemProductSerializer()
    quantity = serializers.IntegerField(min_value=0)
    total_price = serializers.FloatField(source='get_total')


class ToggleCartItemSerializer(serializers.Serializer):
    """ For CRUD cart item data VALIDATION """
    slug = serializers.SlugField()
    quantity = serializers.IntegerField(min_value=0)


class CheckoutSerializer(serializers.Serializer):
    "CheckoutSerializer — это простой сериализатор для валидации данных при оформлении заказа, до создания самого заказа"
    shipping_id = serializers.UUIDField()


class OrderSerializer(serializers.Serializer):
    tx_ref = serializers.CharField()
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    delivery_status = serializers.CharField()
    payment_status = serializers.CharField()
    date_delivered = serializers.DateTimeField()
    shipping_details = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(
        max_digits=100, decimal_places=2, source="get_cart_subtotal"
    )
    total = serializers.DecimalField(
        max_digits=100, decimal_places=2, source="get_cart_total"
    )

    @extend_schema_field(ShippingAddressSerializer)
    def get_shipping_details(self, obj):
        return ShippingAddressSerializer(obj).data


class CheckItemOrderSerializer(serializers.Serializer):
    product = ProductSerializer()
    quantity = serializers.IntegerField()
    total = serializers.FloatField(source="get_total")


class CreateReviewSerializer(serializers.Serializer):
    product_slug = serializers.SlugField()
    rating = serializers.IntegerField()
    text = serializers.CharField(max_length=500)

    def validate_rating(self, value):
        if value not in dict(RATING_CHOICES).keys():
            raise serializers.ValidationError(f"Рейтинг должен быть от {RATING_CHOICES[0][0]} до  {RATING_CHOICES[-1][0]}")
        return value


class ReviewSerializer(serializers.Serializer):
    user = serializers.EmailField(source='user.email', read_only=True)
    product = serializers.SlugField(source='product.slug')
    rating = serializers.IntegerField()
    text = serializers.CharField(max_length=500)
