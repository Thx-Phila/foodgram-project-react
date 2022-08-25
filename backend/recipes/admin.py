from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredientAmount,
    ShoppingCart,
    Subscribe,
    Tag,
)


class RecipeAdmin(admin.ModelAdmin):
    model = Recipe
    readonly_fields = ("added_to_favorites",)
    list_display = (
        "name",
        "author",
    )
    list_display_links = ("name",)
    list_filter = ("author", "name")


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "measurement_unit",
    )
    list_display_links = ("name",)
    list_filter = ("name",)


class TagAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
    )
    list_display_links = ("name",)


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "author",
    )


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "recipe",
    )
    list_filter = ("user",)


class RecipeIngredientAmountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipe",
        "ingredient",
        "amount",
    )
    list_display_links = (
        "id",
        "ingredient",
    )
    list_filter = ("recipe",)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "recipe",
    )
    list_filter = ("user",)


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeIngredientAmount, RecipeIngredientAmountAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Subscribe, SubscriptionAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
