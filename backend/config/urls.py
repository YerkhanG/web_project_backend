from django.urls import include, path

urlpatterns = [
    path("", include("scores.urls")),
]
