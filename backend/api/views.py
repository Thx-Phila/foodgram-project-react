import io

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import Ingredient, Recipe, RecipeIngredientAmount, Tag

from .filters import IngredientFilter, RecipeFilter
from .mixins import ListRetrieveViewSet, ListViewSet
from .permissions import IsOwner, ReadOnly
from .serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    SubscriptionCreateDeleteSerializer,
    SubscriptionSerializer,
    TagSerializer,
)

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        user = request.user

        if request.method == "POST":
            data = {'user': request.user.id, 'author': id}
            serializer = SubscriptionCreateDeleteSerializer(
                data=data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )

        if request.method == "DELETE":
            deleted = user.follower.filter(author_id=id).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            response = {"errors": "Автор не найден в подписках."}
            return Response(
                response, status=status.HTTP_400_BAD_REQUEST
            )


class SubscriptionViewSet(ListViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return user.follower.all()


class IngredientViewSet(ListRetrieveViewSet):
    queryset = Ingredient.objects.get_queryset()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.get_queryset()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (
        (permissions.IsAuthenticated & IsOwner) | ReadOnly,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeSerializer
        return RecipeWriteSerializer

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = False
        return self.update(request, *args, **kwargs)

    def favorite_shopping_cart(
        self, request, pk, model, related, text
    ):
        user = request.user
        model = apps.get_model(app_label="recipes", model_name=model)

        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            response = {"errors": "Рецепт не найден."}
            return Response(
                response, status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == "POST":
            item, is_created = model.objects.get_or_create(
                user=user, recipe=recipe
            )
            if is_created:
                serializer = FavoriteSerializer(recipe)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            response = {"errors": f"Рецепт уже в {text}."}
            return Response(
                response, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = related.get(recipe_id=pk)
        except model.DoesNotExist:
            response = {"errors": f"Рецепт не найден в {text}."}
            return Response(
                response, status=status.HTTP_400_BAD_REQUEST
            )

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        queryset = request.user.recipes_favorite_related
        return self.favorite_shopping_cart(
            request=request,
            pk=pk,
            model="Favorite",
            related=queryset,
            text="избранное",
        )

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        queryset = request.user.recipes_shoppingcart_related
        return self.favorite_shopping_cart(
            request=request,
            pk=pk,
            model="ShoppingCart",
            related=queryset,
            text="список покупок",
        )

    def create_pdf(self, shopping_cart):
        buffer = io.BytesIO()
        page = canvas.Canvas(buffer)

        pdfmetrics.registerFont(TTFont("Hel", "helvetica.ttf"))
        page.setFont("Hel", 24)
        x, y = 50, 800
        page.drawString(x, y + 30, "Список покупок:")
        for ingredient in shopping_cart:
            name, measurement_unit, amount = ingredient.values()
            page.setFont("Hel", 14)
            page.drawString(
                x, y - 10, f"• {name} - {measurement_unit}- {amount}"
            )
            y = y - 25
        page.showPage()
        page.save()
        pdf = buffer.getvalue()
        buffer.close()

        return pdf

    @action(
        methods=["get"],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        user = request.user
        recipes = user.recipes_shoppingcart_related.all().values_list(
            "recipe__pk", flat=True
        )
        shopping_cart = (
            RecipeIngredientAmount.objects.filter(recipe__in=recipes)
            .values(
                "ingredient__name", "ingredient__measurement_unit"
            )
            .annotate(amount=Sum("amount"))
        )

        pdf = self.create_pdf(shopping_cart)
        response = HttpResponse(pdf, content_type="application/pdf")
        content_disposition = 'attachment; filename="list.pdf"'
        response["Content-Disposition"] = content_disposition
        return response
