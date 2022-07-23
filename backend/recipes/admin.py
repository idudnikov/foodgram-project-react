from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .forms import TagForm
from .models import FavoritedRecipe, Ingredient, Recipe, ShoppingCart, Tag


class IngredientResource(resources.ModelResource):
    class Meta:
        model = Ingredient


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    form = TagForm


@admin.register(Ingredient)
class IngredientAdmin(ImportExportModelAdmin):
    resource_class = IngredientResource
    list_display = ("name", "measurement_unit")
    list_filter = ("name",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "count_favorites")
    list_filter = ("author", "name", "tags")

    def count_favorites(self, obj):
        return obj.favorites.count()


admin.site.register(ShoppingCart)
admin.site.register(FavoritedRecipe)
