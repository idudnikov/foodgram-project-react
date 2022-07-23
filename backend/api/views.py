from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from users.models import CustomUser, Subscription
from recipes.models import Tag, Ingredient, Recipe, FavoritedRecipe,\
    ShoppingCart, RecipeIngredient
from .serializers import TagSerializer, ListRetrieveIngredientSerializer, \
    RecipeSerializer, ListRetrieveUserSerializer, \
    CreateUserSerializer, FavoritedRecipeSerializer, SubscriptionSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = ListRetrieveIngredientSerializer
    search_fields = ("name",)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create_recipe_object(self, model, user, pk):
        params = {FavoritedRecipe: "избранное",
                  ShoppingCart: "корзину"}
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response(
                {'errors': f'Ошибка! Данный рецепт уже добавлен в {params[model]}!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = FavoritedRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe_object(self, model, user, pk):
        params = {FavoritedRecipe: "избранного",
                  ShoppingCart: "корзины"}
        object = model.objects.filter(user=user, recipe__id=pk)
        if object.exists():
            object.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': f'Ошибка! Данный рецепт уже удален из {params[model]}!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.create_recipe_object(FavoritedRecipe, request.user, pk)
        elif request.method == 'DELETE':
            return self.delete_recipe_object(FavoritedRecipe, request.user, pk)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.create_recipe_object(ShoppingCart, request.user, pk)
        elif request.method == 'DELETE':
            return self.delete_recipe_object(ShoppingCart, request.user, pk)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients_list = {}
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values_list(
            'ingredient__name', 'ingredient__measurement_unit',
            'amount'
        )
        for ingredient in ingredients:
            ingredients_list[ingredient[0]] = {
                'measurement_unit': ingredient[1],
                'amount': ingredient[2]
            }
        pdfmetrics.registerFont(TTFont('Verdana', 'Verdana.ttf', 'UTF-8'))
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_cart.pdf"')
        page = canvas.Canvas(response)
        page.setFont('Verdana', size=30)
        page.drawString(30, 790, 'Список продуктов для покупки')
        page.setFont('Verdana', size=14)
        height = 750
        for item, (name, data) in enumerate(ingredients_list.items(), 1):
            page.drawString(30, height, (
                f'{item}. {name.capitalize()} - {data["amount"]} '
                f'{data["measurement_unit"]}'))
            height -= 25
        page.showPage()
        page.save()
        return response


class UsersViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ListRetrieveUserSerializer
        return CreateUserSerializer

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(CustomUser, id=pk)
        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response({
                    'errors':
                        'Ошибка! Подписка на данного автора уже оформлена!'
                },
                    status=status.HTTP_400_BAD_REQUEST)
            if user == author:
                return Response(
                    {'errors': 'Ошибка! Подписка на самого себя невозможна!'},
                    status=status.HTTP_400_BAD_REQUEST)
            subscription = Subscription.objects.create(
                user=user, author=author)
            serializer = SubscriptionSerializer(
                subscription, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if user == author:
                return Response(
                    {'errors': 'Ошибка! Отмена подписки на себя невозможна!'},
                    status=status.HTTP_400_BAD_REQUEST)
            subscription = Subscription.objects.filter(
                user=user, author=author)
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Ошибка! Подписка на данного автора уже отменена!'},
                status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = Subscription.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
