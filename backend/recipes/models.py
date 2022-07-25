from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
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

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, verbose_name="Наименование тэга")
    color = models.CharField(
        max_length=7, default="#ffffff", verbose_name="Цветовой HEX-код"
    )
    slug = models.SlugField(unique=True, verbose_name="Slug тэга")

    class Meta:
        ordering = ["name"]
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"

    def __str__(self):
        return self.name


class Recipe(models.Model):
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
        upload_to="recipes/",
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

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
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
        verbose_name = "Ингредиенты рецепта"
        verbose_name_plural = "Ингредиенты рецептов"

    def __str__(self):
        return (
            f'Рецепт "{self.recipe.name}" - '
            f'ингредиент "{self.ingredient.name}"'
        )


class FavoritedRecipe(models.Model):
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
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"

    def __str__(self):
        return (
            f'Избранный рецепт "{self.recipe.name}" пользователя'
            f' "{self.user.username}"'
        )


class ShoppingCart(models.Model):
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
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f'Список покупок пользователя "{self.user.username}"'
