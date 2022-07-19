from django.contrib.auth.tokens import default_token_generator
from django.core.validators import RegexValidator
from django.db.models import Avg
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework.validators import UniqueValidator

from recipes.models import (
    Tag, Ingredient, Recipe, FavoritedRecipe, ShoppingCart,
    RecipeIngredient
)
from users.models import CustomUser, Subscription


class ListRetrieveUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ("email", "id", "username", "first_name", "last_name",
                  "is_subscribed")

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if Subscription.objects.filter(user=user, author=obj.id).exists():
            return True
        return False


class CreateUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all())],
        max_length=254,
        required=True
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all())],
        max_length=150,
        required=True
    )
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(max_length=150, required=True)

    class Meta:
        model = CustomUser
        fields = ("email", "username", "first_name", "last_name", "password")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class ListRetrieveIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.pk')
    name = serializers.StringRelatedField(source='ingredient.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ListRetrieveRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)
    author = ListRetrieveUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredient_recipe', read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "tags", "author", "ingredients", "is_favorited",
                  "is_in_shopping_cart", "name", "image", "text",
                  "cooking_time")

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if FavoritedRecipe.objects.filter(
                user=user, recipe=obj.id).exists():
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if ShoppingCart.objects.filter(
                user=user, recipe=obj.id).exists():
            return True
        return False
