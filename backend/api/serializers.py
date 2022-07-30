from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


class ShortUserSerializer(UserSerializer):

    class Meta:
        model = User
        fields = (
            "email", "id", "username", "first_name", "last_name"
        )


class CustomUserSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        max_length=254,
        required=True,
    )
    id = serializers.IntegerField(required=False)
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        max_length=150,
        required=True,
    )
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(
        max_length=150, required=True, write_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
            "is_subscribed"
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return (
                obj.is_subscribed if hasattr(obj, 'is_subscribed')
                else user.follower.filter(author=obj).exists()
            )
        return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class ListRetrieveIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.pk")
    name = serializers.StringRelatedField(source="ingredient.name")
    measurement_unit = serializers.StringRelatedField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source="recipe_ingredient_recipe", read_only=True, many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        if self.context.get('request').method == 'POST':
            return False
        if self.context.get('request').user.is_authenticated:
            return obj.is_favorited
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context.get('request').method == 'POST':
            return False
        if self.context.get('request').user.is_authenticated:
            return obj.is_in_shopping_cart
        return False

    def validate(self, data):
        added_ingredients = []
        ingredients_data = self.initial_data.get("ingredients")
        for ingredient_item in ingredients_data:
            get_object_or_404(Ingredient, id=ingredient_item["id"])
            if ingredient_item["id"] in added_ingredients:
                raise serializers.ValidationError({
                    "error":
                        f"Ошибка! Нельзя добавлять несколько одинаковых"
                        f" ингредиентов!"
                })
            added_ingredients.append(ingredient_item["id"])
            if type(ingredient_item["amount"]) != int:
                try:
                    item = int(ingredient_item["amount"])
                    if item <= 0:
                        raise serializers.ValidationError({
                            "error":
                                f"Ошибка! Количество ингредиента должно быть "
                                f"больше нуля!"
                        })
                except ValueError:
                    raise serializers.ValidationError({
                        "error":
                            f"Ошибка! Количество ингредиента должно быть "
                            f"числом!"
                    })
        data["ingredients"] = ingredients_data
        return data

    def serialize_ingredients_data(self, ingredients_data, recipe):
        for ingredient in ingredients_data:
            RecipeIngredient.objects.create(
                ingredient_id=ingredient.get("id"),
                amount=ingredient.get("amount"),
                recipe=recipe,
            )

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags_data = self.initial_data.get("tags")
        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)
        self.serialize_ingredients_data(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags_data = self.initial_data.get("tags")
        super().update(instance, validated_data)
        instance.tags.set(tags_data)
        RecipeIngredient.objects.filter(recipe=instance).all().delete()
        self.serialize_ingredients_data(ingredients_data, instance)
        return instance


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = request.GET.get("recipes_limit")
        queryset = Recipe.objects.filter(author=obj.id)
        if recipes_limit:
            queryset = queryset[: int(recipes_limit)]
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes_count
