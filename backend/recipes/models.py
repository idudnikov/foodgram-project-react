from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    """
    Класс, описывающий модель Ингредиента.
    """

    name = models.CharField(
        max_length=200, verbose_name="Наименование ингредиента"
    )
    measurement_unit = models.CharField(
        max_length=50, verbose_name="Единица измерения"
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


class Tag(models.Model):
    """
    Класс, описывающий модель Тэга.
    """

    name = models.CharField(max_length=100, verbose_name="Наименование тэга")
    color = models.CharField(
        max_length=7, default="#ffffff", verbose_name="Цветовой HEX-код"
    )
    slug = models.SlugField(unique=True, verbose_name="Slug тэга")

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"


class Recipe(models.Model):
    """
    Класс, описывающий модель Рецепта.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор рецепта",
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Название рецепта",
        blank=False,
        null=False,
    )
    image = models.ImageField(
        upload_to="recipes/media/",
        verbose_name="Изображение",
        blank=False,
        null=False,
    )
    text = models.TextField(
        "Описание рецепта",
        help_text="Введите описание рецепта",
        blank=False,
        null=False,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name="recipe",
        verbose_name="Ингредиент",
        through="RecipeIngredient",
    )
    tags = models.ManyToManyField(
        Tag, related_name="recipe", verbose_name="Тэг"
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления", blank=False, null=False
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class RecipeIngredient(models.Model):
    """
    Класс, описывающий количество Ингредиента в Рецепте.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredient_recipe",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredient_ingredient",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        default=1, verbose_name="Количество"
    )

    class Meta:
        verbose_name = "Количество ингредиента"
        verbose_name_plural = "Количество ингредиентов"


class FavoritedRecipe(models.Model):
    """
    Класс, описывающий Рецепты, добавленные пользователем в избранное.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorited_recipe",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorited_recipe",
        verbose_name="Рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="Нельзя добавлять рецепт в избранное более одного раза",
            )
        ]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"


class ShoppingCart(models.Model):
    """
    Класс, описывающий корзину покупок пользователя.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="Нельзя добавлять рецепт в коризну более одного раза",
            )
        ]
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
