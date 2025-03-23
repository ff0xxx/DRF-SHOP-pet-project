from django.urls import path

from apps.shop.views import CategoriesView, ProductsByCategoryView, ProductsBySellerView, ProductsView, ProductView, \
                                CartView, CheckoutView, OrderView, OrderItemView, ReviewsView, CreateReviewView


urlpatterns = [
    path("categories/", CategoriesView.as_view()),
    path("categories/<slug:slug>/", ProductsByCategoryView.as_view()),
    path("sellers/<slug:slug>/", ProductsBySellerView.as_view()),
    path("products/", ProductsView.as_view()),

    path("products/reviews/<slug:slug>/", ReviewsView.as_view()),
    path("products/reviews/", CreateReviewView.as_view()),

    path("products/<slug:slug>/", ProductView.as_view()),
    path("cart/", CartView.as_view()),
    path("checkout/", CheckoutView.as_view()),
    path("orders/", OrderView.as_view()),
    path("orders/<str:tx_ref>/", OrderItemView.as_view()),
]