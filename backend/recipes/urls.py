from django.urls import include, path
from recipes.views import (FavoritesOrShopingViewSet, IngredientViewSet,
                           RecipeViewSet, TagViewSet, download_shopping_cart)
from rest_framework.routers import DefaultRouter

app_name = 'recipes'

router_v1 = DefaultRouter()

router_v1.register(r'recipes', RecipeViewSet)
router_v1.register(r'recipes', FavoritesOrShopingViewSet, basename='recipes')
router_v1.register(r'tags', TagViewSet)
router_v1.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    path('recipes/download_shopping_cart/',
         download_shopping_cart,
         name='download_shopping_cart'),
    path('', include(router_v1.urls)),
]
