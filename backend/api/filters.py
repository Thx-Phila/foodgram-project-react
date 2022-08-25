from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe
from users.models import User


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="startswith")

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(filters.FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            marked_recipes = Recipe.marked.favorited_shoppingcart(
                self.request.user
            )
            return marked_recipes.filter(is_favorited=True).all()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            marked_recipes = Recipe.marked.favorited_shoppingcart(
                self.request.user
            )
            return marked_recipes.filter(
                is_in_shopping_cart=True
            ).all()
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags')
