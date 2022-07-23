from django.contrib import admin

from .models import Ingredient, Recipe, Tag, ShoppingCart, FavoritedRecipe
from .forms import TagForm


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    form = TagForm


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags')


admin.site.register(ShoppingCart)
admin.site.register(FavoritedRecipe)
