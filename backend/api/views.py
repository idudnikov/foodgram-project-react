from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (
    FavoritedRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription

from .filters import IngredientSearchFilter, RecipesFilter
from .pagination import CustomPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    CreateUserSerializer,
    ListRetrieveIngredientSerializer,
    ListRetrieveUserSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    SubscriptionSerializer,
    TagSerializer,
)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = ListRetrieveIngredientSerializer
    filter_backends = (IngredientSearchFilter,)
    search_fields = ("^name",)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipesFilter
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            permission_classes = (AllowAny,)
        elif self.action in ('update', 'destroy', 'partial_update'):
            permission_classes = (IsOwnerOrReadOnly,)
        else:
            permission_classes = (IsAuthenticated,)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            is_favorited = user.favorited_recipe.filter(id=OuterRef('id'))
            is_in_shopping_cart = user.shopping_cart.filter(
                id=OuterRef('id'))
            return Recipe.objects.annotate(
                is_favorited=Exists(is_favorited),
                is_in_shopping_cart=Exists(is_in_shopping_cart)
            )
        queryset = (
            Recipe.objects.select_related("author").all()
            .prefetch_related("tags", "ingredients")
        )
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create_recipe_object(self, model, user, pk):
        params = {FavoritedRecipe: "избранное", ShoppingCart: "корзину"}
        if model.objects.filter(user=user, recipe__id=pk).exists():
            raise ValidationError({
                "errors":
                    f"Ошибка! Данный рецепт уже добавлен в {params[model]}!"
            })
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe_object(self, model, user, pk):
        params = {FavoritedRecipe: "избранного", ShoppingCart: "корзины"}
        object = model.objects.filter(user=user, recipe__id=pk)
        if object.exists():
            object.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError({
            "errors":
                f"Ошибка! Данный рецепт уже удален из {params[model]}!"
        })

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        if request.method == "POST":
            return self.create_recipe_object(FavoritedRecipe, request.user, pk)
        elif request.method == "DELETE":
            return self.delete_recipe_object(FavoritedRecipe, request.user, pk)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        if request.method == "POST":
            return self.create_recipe_object(ShoppingCart, request.user, pk)
        elif request.method == "DELETE":
            return self.delete_recipe_object(ShoppingCart, request.user, pk)

    @action(
        methods=["get"], detail=False, permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients_list = {}
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values_list(
            "ingredient__name", "ingredient__measurement_unit", "amount"
        )
        for ingredient in ingredients:
            ingredient_name = ingredient[0]
            if ingredient_name not in ingredients_list:
                ingredients_list[ingredient_name] = {
                    "measurement_unit": ingredient[1],
                    "amount": ingredient[2],
                }
            else:
                ingredients_list[ingredient_name]["amount"] += ingredient[2]
        pdfmetrics.registerFont(TTFont("Verdana", "Verdana.ttf", "UTF-8"))
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            "attachment; " 'filename="shopping_cart.pdf"'
        )
        page = canvas.Canvas(response)
        page.setFont("Verdana", size=30)
        page.drawString(30, 790, "Список продуктов для покупки")
        page.setFont("Verdana", size=14)
        height = 750
        for item, (name, data) in enumerate(ingredients_list.items(), 1):
            page.drawString(
                30,
                height,
                (
                    f'{item}. {name.capitalize()} - {data["amount"]} '
                    f'{data["measurement_unit"]}'
                ),
            )
            height -= 25
        page.showPage()
        page.save()
        return response


class UsersViewSet(UserViewSet):
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            is_subscribed = user.follower.filter(author=OuterRef('id'))
            return User.objects.annotate(is_subscribed=Exists(is_subscribed))
        return User.objects.all()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ListRetrieveUserSerializer
        return CreateUserSerializer

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == "POST":
            if Subscription.objects.filter(user=user, author=author).exists():
                raise ValidationError({
                    "errors":
                        "Ошибка! Подписка на данного автора уже оформлена!"
                })
            if user == author:
                raise ValidationError({
                    "errors":
                        "Ошибка! Подписка на самого себя невозможна!"
                })
            subscription = Subscription.objects.create(
                user=user, author=author
            )
            serializer = SubscriptionSerializer(
                subscription.author, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            if user == author:
                raise ValidationError({
                    "errors":
                        "Ошибка! Отмена подписки на себя невозможна!"
                })
            subscription = Subscription.objects.filter(
                user=user, author=author
            )
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise ValidationError({
                "errors":
                    "Ошибка! Подписка на данного автора уже отменена!"
            })

    @action(
        methods=["get"], detail=False, permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        pagination = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pagination, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)
