from django.urls import path

from .views import MovesView

app_name = "tribunales"
urlpatterns = [
    path("", MovesView.as_view(), name="moves"),
]
