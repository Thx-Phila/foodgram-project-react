import base64
import imghdr
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredientAmount,
    ShoppingCart,
    Subscribe,
    Tag,
)

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and user.follower.filter(author=obj).exists()
        )


class UserWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientAmountSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredientAmount
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientAmountWriteSerializer(
    serializers.ModelSerializer
):

    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredientAmount
        fields = ("id", "amount")


class RecipeSerializer(serializers.ModelSerializer):

    author = UserReadSerializer()
    ingredients = RecipeIngredientAmountSerializer(
        source="recipeingredientamount", many=True
    )
    tags = TagSerializer(many=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "author",
            "text",
            "tags",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "image",
            "cooking_time",
        )

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.image:
            response["image"] = instance.image.url
        return response

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and Favorite.objects.filter(
                user=user, recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and ShoppingCart.objects.filter(
                user=user, recipe=obj
            ).exists()
        )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            if "data:" in data and ";base64," in data:
                header, data = data.split(";base64,")

            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail("invalid_image")

            file_name = str(uuid.uuid4())
            file_extension = self.get_file_extension(
                file_name, decoded_file
            )
            fullname = f"{file_name}.{file_extension}"
            data = ContentFile(decoded_file, name=fullname)

        return super().to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension
        return extension


class RecipeWriteSerializer(serializers.ModelSerializer):

    ingredients = RecipeIngredientAmountWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(max_length=None, use_url=True)
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
            "author",
        )

    def validate(self, data):
        ingredients = data['ingredients']
        ingredients_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    {'ingredients': 'Только уникальные ингредиенты'}
                )
            ingredients_list.append(ingredient_id)
            amount = ingredient['amount']
            if int(amount) <= 0:
                raise serializers.ValidationError(
                    {'amount': 'Должен быть хотя-бы один ингредиент'}
                )

        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Нужно указать минимум один тег'}
            )
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError(
                    {'tags': 'Теги должны быть уникальны'}
                )
            tags_list.append(tag)

        cooking_time = data['cooking_time']
        if int(cooking_time) <= 0:
            raise serializers.ValidationError(
                {'cooking_time': 'Время приготовление больше 0'}
            )
        return data

    def create(self, validated_data):
        ing_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")

        recipe = Recipe.objects.create(**validated_data)
        amounts = self.get_amounts(recipe, ing_data)
        RecipeIngredientAmount.objects.bulk_create(amounts)

        for data in tags_data:
            tag = get_object_or_404(Tag, id=data.id)
            recipe.tags.add(tag)

        recipe.save()
        return recipe

    def update(self, instance, validated_data):
        ing_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")

        instance = super().update(instance, validated_data)
        instance.recipeingredientamount.all().delete()
        amounts = self.get_amounts(instance, ing_data)
        RecipeIngredientAmount.objects.bulk_create(amounts)

        tags = []
        for data in tags_data:
            tag = get_object_or_404(Tag, id=data.id)
            tags.append(tag)
        instance.tags.set(tags)

        return instance

    def get_amounts(self, recipe, ingredients_data):
        amounts = [
            RecipeIngredientAmount(
                recipe=recipe,
                ingredient=get_object_or_404(
                    Ingredient, id=ing_data["id"]
                ),
                amount=ing_data["amount"],
            )
            for ing_data in ingredients_data
        ]
        return amounts

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source="author.id", required=False)
    username = serializers.CharField(source="author.username")
    first_name = serializers.CharField(source="author.first_name")
    last_name = serializers.CharField(source="author.last_name")
    email = serializers.EmailField(source="author.email")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        author = obj.author
        return (
            user.is_authenticated
            and Subscribe.objects.filter(
                user=user, author=author
            ).exists()
        )

    def get_recipes(self, obj):
        query_params = self.context["request"].query_params
        limit = query_params.get(
            "recipes_limit", settings.REST_FRAMEWORK["PAGE_SIZE"]
        )
        recipes_page = query_params.get("recipes_page", 1)

        paginator = Paginator(obj.author.recipes.all(), limit)
        recipes = paginator.page(recipes_page)
        serializer = FavoriteSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.author.recipes.all().count()


class SubscriptionCreateDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ['user', 'author']

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на себя'}
            )
        if Subscribe.objects.filter(
            user=data['user'], author=data['author']
        ).exists():
            raise serializers.ValidationError(
                {'errors': 'Вы уже подписаны на данного пользователя'}
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return SubscriptionSerializer(instance, context=context).data
