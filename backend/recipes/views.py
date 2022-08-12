from django.db.models import Count, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from recipes.filters import IngredientSearchFilter, RecipeFilter
from recipes.models import (Favourite, Follow, Ingredient, Recipe,
                            ShoppingCart, Tag)
from recipes.paginator import LimitPageNumberPagination
from recipes.permissions import AuthorOrReadPermission, IsAdminOrReadOnly
from recipes.serializers import (IngredientSerializer,
                                 RecipeGETShortSerializer,
                                 RecipePOSTSerializer, RecipeSerializer,
                                 TagSerializer, UserFollowSerializer)
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import User


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [AuthorOrReadPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = LimitPageNumberPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipePOSTSerializer


class FavoritesOrShopingViewSet(viewsets.ModelViewSet):

    def create_or_del_recipe_in_db(self, request, pk, database):
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=pk)
            if not database.objects.filter(
                    user=self.request.user,
                    recipe=recipe).exists():
                database.objects.create(
                    user=self.request.user,
                    recipe=recipe)
                serializer = RecipeGETShortSerializer(recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            text = 'errors: Объект уже в списке.'
            return Response(text, status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            if database.objects.filter(
                    user=self.request.user,
                    recipe=recipe).exists():
                database.objects.filter(
                    user=self.request.user,
                    recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            text = 'errors: Объект не в списке.'
            return Response(text, status=status.HTTP_400_BAD_REQUEST)
        else:
            text = 'errors: Метод обращения недопустим.'
            return Response(text, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=(
            'post',
            'delete'
        ),
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self.create_or_del_recipe_in_db(request, pk, Favourite)

    @action(
        detail=True,
        methods=(
            'post',
            'delete'
        ),
    )
    def shopping_cart(self, request, pk=None):
        return self.create_or_del_recipe_in_db(request, pk, ShoppingCart)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class FollowViewSet(viewsets.ModelViewSet):

    @action(
        detail=True,
        methods=(
            'post',
            'delete'
        ),
    )
    def subscribe(self, request, pk=None):
        if request.method == 'POST':
            if pk == self.request.user.id:
                text = 'errors: Нельзя подписаться на самого себя.'
                return Response(text, status=status.HTTP_400_BAD_REQUEST)
            if not Follow.objects.filter(
                    user=self.request.user,
                    following_id=pk).exists():
                Follow.objects.create(
                    user=self.request.user,
                    following_id=pk)
                follow = User.objects.filter(id=pk).annotate(
                    recipes_count=Count('recipe'))
                serializer = UserFollowSerializer(follow,
                                                  context={'request': request},
                                                  many=True)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            text = 'errors: Объект уже в списке.'
            return Response(text, status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            following = get_object_or_404(User, id=pk)
            if Follow.objects.filter(
                    user=self.request.user,
                    following=following).exists():
                Follow.objects.filter(
                    user=self.request.user,
                    following=following).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            text = 'errors: Объект не в списке.'
            return Response(text, status=status.HTTP_400_BAD_REQUEST)
        else:
            text = 'errors: Метод обращения недопустим.'
            return Response(text, status=status.HTTP_400_BAD_REQUEST)


class FollowGETAPIView(ListAPIView):
    pagination_class = LimitPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get(self, request):
        follow = User.objects.filter(
            following__user=request.user).annotate(
                recipes_count=Count('recipe'))
        paginate = self.paginate_queryset(follow)
        serializer = UserFollowSerializer(paginate,
                                          context={'request': request},
                                          many=True)
        return self.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    ingredients = (
        Ingredient.objects.filter(
            ingridient_for_recipe__recipe__shopping_cart__user=request.user
        )
        .annotate(sum_amount=Sum("ingridient_for_recipe__amount"))
        .values_list("name", "sum_amount", "measurement_unit")
    )
    shoping_list = []
    for ingredient in ingredients:
        shoping_list.append(
            f'{ingredient[0]} - {ingredient[1]} {ingredient[2]}.\n')
    filename = 'my_shopping_list.txt'
    response = HttpResponse(shoping_list, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(
        filename)
    return response
