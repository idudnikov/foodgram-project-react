from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, filters
from recipes.models import Recipe
from rest_framework.filters import SearchFilter

User = get_user_model()


class RecipesFilter(FilterSet):
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")
    is_favorited = filters.BooleanFilter(method="filter_favorited")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_shopping_cart")

    class Meta:
        model = Recipe
        fields = ("tags", "author")

    def filter_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorited_recipe__user=self.request.user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset


class IngredientSearchFilter(SearchFilter):
    search_param = "name"
