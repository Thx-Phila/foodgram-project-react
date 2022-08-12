from recipes.fields import Base64ImageField
from recipes.models import (Favourite, Ingredient, IngredientForRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.models import User
from users.serializers import CustomUserSerializer


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientForRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientForRecipe
        fields = fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientPOSTSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientForRecipe
        fields = ('id', 'amount')


class RecipePOSTSerializer(serializers.ModelSerializer):
    ingredients = IngredientPOSTSerializer(many=True,
                                           source='recipe_for_ingridient')
    image = Base64ImageField(max_length=None, use_url=True)
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'image',
                  'name',
                  'text',
                  'cooking_time', )
        model = Recipe
        extra_kwargs = {
            'id': {'read_only': True},
        }

    def validate(self, data):
        ingredients = data.get('recipe_for_ingridient')
        if not ingredients:
            raise serializers.ValidationError({
                'errors': 'Выберите хотя бы один ингредиент!'
            })
        ingredients_list = []
        for ingredient in ingredients:
            ingredient_obj = ingredient['id']
            if ingredient_obj in ingredients_list:
                raise serializers.ValidationError({
                    'errors': 'Ингредиент не должен повторяться!'
                })
            ingredients_list.append(ingredient_obj)
            amount = ingredient['amount']
            if amount <= 0:
                raise serializers.ValidationError({
                    'errors': 'Количество ингридиента должно быть больше нуля.'
                })

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'errors': 'Выберите хотя бы один тэг!'
            })
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError({
                    'errors': 'Тэг не должен повторяться!'
                })
            tags_list.append(tag)
        return data

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

    def create_ingredients(self, ingredients, recipe):
        IngredientForRecipe.objects.bulk_create(
            [
                IngredientForRecipe(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'],
                )
                for ingredient in ingredients
            ]
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_for_ingridient')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        ingredients = validated_data.pop('recipe_for_ingridient')
        IngredientForRecipe.objects.filter(recipe_id=instance.id).delete()
        self.create_ingredients(ingredients, instance)
        super().update(instance, validated_data)
        return instance

    def validate_cooking_time(self, value):
        min_time = 1
        if (value < min_time):
            raise serializers.ValidationError(
                f'Время приготовления должно быть больше {min_time} мин.!'
            )
        return value


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientForRecipeSerializer(read_only=True,
                                                many=True,
                                                source='recipe_for_ingridient')
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'name',
                  'image',
                  'text',
                  'cooking_time',)

    def get_is_favorited(self, obj):
        user = self.context['request'].user.id
        recipe = obj.id
        return Favourite.objects.filter(user_id=user,
                                        recipe_id=recipe).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user.id
        recipe = obj.id
        return ShoppingCart.objects.filter(user_id=user,
                                           recipe_id=recipe).exists()


class RecipeGETShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time',)


class UserFollowSerializer(CustomUserSerializer):

    recipes = RecipeGETShortSerializer(many=True,
                                       read_only=True,
                                       source='recipe_set')
    recipes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
