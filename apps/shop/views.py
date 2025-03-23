from rest_framework.views       import APIView
from rest_framework.response    import Response
from drf_spectacular.utils      import extend_schema
from rest_framework.pagination  import PageNumberPagination

from apps.shop.serializers  import CategorySerializer, ProductSerializer, OrderItemSerializer, ToggleCartItemSerializer, \
                                    CheckoutSerializer, OrderSerializer, CheckItemOrderSerializer, ReviewSerializer, CreateReviewSerializer
from apps.shop.models       import Category, Product, Review
from apps.sellers.models    import Seller
from apps.profiles.models   import ShippingAddress, Order, OrderItem
from apps.common.pagination import CustomPagination
from apps.common.utils      import set_dict_attr
from apps.shop.filters      import ProductFilter
from apps.shop.schema_examples import PRODUCT_PARAM_EXAMPLE


tags = ['Shop']


class CategoriesView(APIView):
    serializer_class = CategorySerializer

    @extend_schema(
        summary="Categories Fetch",
        description="This endpoint returns all categories",
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        serializer = self.serializer_class(categories, many=True)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Category Create",
        description="This endpoint creates categories",
        tags=tags,
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            new_cat = Category.objects.create(**data)
            serializer = self.serializer_class(new_cat)
            return Response(data=serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)


class ProductsByCategoryView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="category_products",
        summary="Category Products Fetch",
        description="This endpoint returns all products in a particular category",
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        category = Category.objects.get_or_none(slug=kwargs["slug"])
        if not category:
            return Response(data={"message": "Category does not exist!"}, status=404)

        products = Product.objects.select_related("category", "seller", "seller__user").filter(category=category)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


class ProductsView(APIView):
    serializer_class = ProductSerializer
    pagination_class = CustomPagination

    @extend_schema(
        operation_id="all_products",
        summary="Product Fetch",
        description="This endpoint returns all products",
        tags=tags,
        parameters=PRODUCT_PARAM_EXAMPLE,
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related("category", "seller", "seller__user").all()
        filterset = ProductFilter(request.query_params, queryset=products)
        if filterset.is_valid():
            queryset = filterset.qs
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = self.serializer_class(paginated_queryset, many=True)
            return paginator.get_paginated_response(data=serializer.data)
        else:
            return Response(data=filterset.errors, status=400)


class ProductsBySellerView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Seller Products Fetch",
        description="This endpoint returns all products in a particular seller",
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(slug=kwargs["slug"])
        if not seller:
            return Response(data={"message": "Seller does not exist!"}, status=404)

        products = Product.objects.select_related("category", "seller", "seller__user").filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


class ProductView(APIView):
    serializer_class = ProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        operation_id="product_detail",
        summary="Product Details Fetch",
        description="This endpoint returns the details for a product via the slug",
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        product = self.get_object(kwargs['slug'])
        if not product:
            return Response(data={"message": "Product does not exist!"}, status=404)

        serializer = self.serializer_class(product)
        return Response(data=serializer.data, status=200)


class CartView(APIView):
    serializer_class = OrderItemSerializer

    @extend_schema(
        summary="Cart Items Fetch",
        description="This endpoint returns all items in a user cart",
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None).select_related(
            "product", "product__seller", "product__seller__user"
        )
        serializer = self.serializer_class(orderitems, many=True)
        return Response(data=serializer.data)

    @extend_schema(
        summary="Toggle Item in cart",
        description="""
            This endpoint allows a user or guest to add/update/remove an item in cart
            If quantity is 0, the item is removed from cart
        """,
        tags=tags,
        request=ToggleCartItemSerializer,
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ToggleCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        quantity = data['quantity']

        product = Product.objects.select_related('seller', 'seller__user').get_or_none(slug=data['slug'])
        if not product:
            return Response({'message': 'No Product with that slug'}, status=404)

        orderitem, created = OrderItem.objects.update_or_create(
            user=user,
            order_id=None,
            product=product,
            defaults={'quantity': quantity},
        )

        resp_message_substring  = 'Updated In'
        status_code = 200
        if created:
            status_code = 201
            resp_message_substring = "Added To"
        if orderitem.quantity == 0:
            resp_message_substring  = 'Removed From'
            orderitem.delete()
            data = None
        if resp_message_substring  != 'Removed From':
            serializer = self.serializer_class(orderitem)
            data = serializer.data
        return Response(data={'message': f'Item {resp_message_substring } Cart', 'item': data}, status=status_code)
        

class CheckoutView(APIView):
    serializer_class = CheckoutSerializer

    @extend_schema(
        summary='Checkout',
        description="This endpoint allows a user to create an order through which payment can then be made through",
        tags=tags,
        request=CheckoutSerializer,
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None)
        if not orderitems.exists():
            return Response({'message': 'No Items in Cart'}, status=404)
            
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        shipping_id = data.get('shipping_id')
        if shipping_id:
            shipping = ShippingAddress.objects.get_or_none(id=shipping_id)
            if not shipping:
                return Response({'message': 'No Shipping Address with this ID'}, status=404)
        else:
            return Response({'message': 'S T O P: django.db.utils.IntegrityError: FOREIGN KEY constraint failed'})
        
        fields_to_update = [
            "full_name",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "zipcode",
        ]
        data = {}
        for field in fields_to_update:
            value = getattr(shipping, field)
            data[field] = value

        order = Order.objects.create(user=user, **data)
        orderitems.update(order=order)

        serializer = OrderSerializer(order)
        return Response(data={"message": "Checkout Successful", "item": serializer.data}, status=200)


class OrderView(APIView):
    serializer_class = OrderSerializer

    @extend_schema(
        operation_id='orders_view',
        summary='Orders Fetch',
        description="This endpoint returns all orders for a particular user",
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        orders = Order.objects.filter(user=user) \
                .prefetch_related('orderitems', 'orderitems__product') \
                .order_by('-created_at')

        serializer = self.serializer_class(orders, many=True)
        return Response(data=serializer.data, status=200)


class OrderItemView(APIView):
    serializer_class = CheckItemOrderSerializer

    @extend_schema(
        operation_id='orders_items_view',
        summary='Order Items Fetch',
        description="This endpoint returns all items of order for a particular user",
        tags=tags,
    )
    def get(self, request, **kwargs):
        order = Order.objects.get_or_none(tx_ref=kwargs['tx_ref'])
        if not order or order.user != request.user:
            return Response(data={'message': 'Order does not exist!'}, status=404)
        orderitems = OrderItem.objects.filter(order=order)

        serializer = self.serializer_class(orderitems, many=True)
        return Response(data=serializer.data, status=200)
    

class ReviewsView(APIView):
    serializer_class = ReviewSerializer

    @extend_schema(
        summary='Reviews Fetch',
        description="This endpoint returns all product's reviews",
        tags=tags,
    )
    def get(self, request, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get_or_none(slug=product_slug)
        if not product:
            return Response({'message': 'Product with this slug does not exist!'}, status=404)

        reviews = product.reviews.all()
        serializer = self.serializer_class(reviews, many=True)
        return Response(data=serializer.data)

    def delete(self, request, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get_or_none(slug=product_slug)
        if not product:
            return Response({'message': 'Product with this slug does not exist!'}, status=404)

        if not product.reviews.filter(user=request.user).exists():
            return Response({'message': 'You did not reviewed this product!'}, status=400)

        Review.objects.get(product=product, user=request.user).delete()
        return Response(data={'message': 'Review deleted successfully'}, status=204)


class CreateReviewView(APIView):
    serializer_class = CreateReviewSerializer

    @extend_schema(
        summary='Create Review Fetch',
        description="This endpoint allows to create a product review",
        tags=tags,
        request=CreateReviewSerializer,
    )
    def post(self, request, *args, **kwargs):
        data = request.data
        product_slug = data.get('product_slug')
        product = Product.objects.get_or_none(slug=product_slug)
        if not product:
            return Response({'message': 'Product with this slug does not exist!'}, status=404)

        if product.reviews.filter(user=request.user).exists():
            return Response({'message': 'You have already reviewed this product!'}, status=400)

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.validated_data.pop('product_slug')
            review = Review.objects.create(user=request.user, product=product, **serializer.validated_data)
            serializer = ReviewSerializer(review)
            return Response(data=serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, *args, **kwargs):
        data = request.data
        product_slug = data.get('product_slug')
        product = Product.objects.get_or_none(slug=product_slug)
        if not product:
            return Response({'message': 'Product with this slug does not exist!'}, status=404)

        if not product.reviews.filter(user=request.user).exists():
            return Response({'message': 'You did not reviewed this product!'}, status=400)

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            data = serializer.validated_data
            review = Review.objects.get(user=request.user, product=product)
            review = set_dict_attr(review, data)
            review.save()
            return Response({'message': 'Your review successfully updated!'}, status=200)

        return Response(serializer.errors, status=400)
