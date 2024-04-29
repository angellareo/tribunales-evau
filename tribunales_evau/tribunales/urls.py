from django.urls import path

from .views import MovesView, MovesXLSView

app_name = "tribunales"
urlpatterns = [
    path("", MovesView.as_view(), name="moves"),
    path("get-xls/", MovesXLSView.as_view(), name="get_xls"),
]
