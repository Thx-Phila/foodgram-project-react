from django.contrib import admin

from .models import (Favourite, Follow, Ingredient, IngredientForRecipe,
                     Recipe, ShoppingCart, Tag)

admin.site.register(IngredientForRecipe)
admin.site.register(Favourite)
admin.site.register(Follow)
admin.site.register(ShoppingCart)


class TagAdmin(admin.ModelAdmin):
    list_display = ('colored_name', 'slug', 'color')
    search_fields = ('name',)


admin.site.register(Tag, TagAdmin)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name',)


admin.site.register(Ingredient, IngredientAdmin)


class IngredientForRecipeInline(admin.TabularInline):
    model = IngredientForRecipe
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    date_hierarchy = 'pub_date'
    list_display = ('name', 'author', 'count_in_favorite')
    search_fields = ('username', 'email')
    list_filter = ('name', 'author', 'tags',)
    empty_value_display = '-пусто-'
    autocomplete_fields = ['tags']
    inlines = (IngredientForRecipeInline,)

    def count_in_favorite(self, obj):
        return obj.in_favorite.count()


admin.site.register(Recipe, RecipeAdmin)
