from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")

    measurement_unit = models.CharField(
        max_length=200, verbose_name="Единица измерения"
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient_measurement",
            ),
        ]

    def __str__(self):
        return f"{self.name}"


class Tag(models.Model):
    name = models.CharField(
        max_length=200, unique=True, verbose_name="Название"
    )
    color = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Цветовой HEX-код",
    )
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return f"{self.name}"


class RecipeQuerySet(models.QuerySet):
    def favorited_shoppingcart(self, user):
        return self.annotate(
            is_favorited=models.Exists(
                Favorite.objects.filter(
                    user=user, recipe_id=models.OuterRef('pk')
                )
            ),
            is_in_shopping_cart=models.Exists(
                ShoppingCart.objects.filter(
                    user=user, recipe_id=models.OuterRef('pk')
                )
            ),
        )


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(max_length=200, verbose_name="Название")
    image = models.ImageField(
        upload_to="recipes/images/", verbose_name="Картинка"
    )
    text = models.TextField(verbose_name="Текстовое описание")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredientAmount",
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(Tag, verbose_name="Теги")
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата публикации"
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления блюда',
    )
    objects = models.Manager()
    marked = RecipeQuerySet.as_manager()

    @property
    def added_to_favorites(self):
        return Favorite.objects.filter(recipe=self.id).count()

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return f"{self.name}"


class RecipeIngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
    )
    amount = models.PositiveIntegerField(
        'Количество',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipeingredientamount",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Количество"

    def __str__(self):
        return f"{self.ingredient} {self.amount}"


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )
    created = models.DateTimeField("Дата подписки", auto_now_add=True)

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_subscription"
            ),
        ]

    def __str__(self):
        return f"{self.user} {self.author}"


class FavoriteShoppingCartBaseModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name="Рецепт"
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.user} {self.recipe}"


class Favorite(FavoriteShoppingCartBaseModel):
    class Meta(FavoriteShoppingCartBaseModel.Meta):
        verbose_name = "Избранное"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite"
            ),
        ]


class ShoppingCart(FavoriteShoppingCartBaseModel):
    class Meta(FavoriteShoppingCartBaseModel.Meta):
        verbose_name = "Список покупок"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shoppingcart"
            ),
        ]
