from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("health/", views.health, name="health"),
    path("api/scores/", views.submit_score, name="submit-score"),
    path("api/leaderboard/", views.leaderboard, name="leaderboard"),
    path("api/players/<str:name>/", views.player_detail, name="player-detail"),
    path("api/stats/", views.stats, name="stats"),
]
