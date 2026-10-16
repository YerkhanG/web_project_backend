import json
import re

from django.db import connection
from django.db.models import Avg, Count, Max
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import Player, Score

DEFAULT_GAME = "arcade"
MAX_POINTS = 1_000_000_000
PLAYER_NAME_RE = re.compile(r"^[\w .-]{1,32}$")


def _error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def _rank_of(game, best):
    better_players = (
        Score.objects.filter(game=game)
        .values("player")
        .annotate(best=Max("points"))
        .filter(best__gt=best)
        .count()
    )
    return better_players + 1


def index(request):
    return render(request, "scores/index.html")


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "error", "database": "down"}, status=503)
    return JsonResponse({"status": "ok", "database": "up"})


@require_POST
def submit_score(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error("Body must be valid JSON.")
    if not isinstance(data, dict):
        return _error("Body must be a JSON object.")

    name = data.get("player")
    game = data.get("game", DEFAULT_GAME)
    points = data.get("points")

    if not isinstance(name, str) or not PLAYER_NAME_RE.match(name.strip()):
        return _error(
            "'player' must be 1-32 characters: letters, digits, spaces, '.', '-' or '_'."
        )
    if not isinstance(game, str) or not 1 <= len(game.strip()) <= 50:
        return _error("'game' must be a string of 1-50 characters.")
    if isinstance(points, bool) or not isinstance(points, int) or not 0 <= points <= MAX_POINTS:
        return _error(f"'points' must be an integer between 0 and {MAX_POINTS}.")

    name, game = name.strip(), game.strip()
    player, _ = Player.objects.get_or_create(name=name)

    previous_best = Score.objects.filter(player=player, game=game).aggregate(
        best=Max("points")
    )["best"]
    Score.objects.create(player=player, game=game, points=points)
    personal_best = points if previous_best is None else max(previous_best, points)

    return JsonResponse(
        {
            "player": player.name,
            "game": game,
            "points": points,
            "personal_best": personal_best,
            "new_personal_best": previous_best is None or points > previous_best,
            "rank": _rank_of(game, personal_best),
        },
        status=201,
    )


@require_GET
def leaderboard(request):
    game = request.GET.get("game", DEFAULT_GAME)
    try:
        limit = int(request.GET.get("limit", 10))
    except ValueError:
        return _error("'limit' must be an integer.")
    limit = max(1, min(limit, 100))
    rows = (
        Score.objects.filter(game=game)
        .values("player__name")
        .annotate(best_score=Max("points"), games_played=Count("id"))
        .order_by("-best_score", "player__name")[:limit]
    )

    entries = []
    rank, previous_score = 0, None
    for position, row in enumerate(rows, start=1):
        if row["best_score"] != previous_score:  # equal scores share a rank (1, 2, 2, 4)
            rank, previous_score = position, row["best_score"]
        entries.append(
            {
                "rank": rank,
                "player": row["player__name"],
                "best_score": row["best_score"],
                "games_played": row["games_played"],
            }
        )
    return JsonResponse({"game": game, "leaderboard": entries})


@require_GET
def player_detail(request, name):
    try:
        player = Player.objects.get(name=name)
    except Player.DoesNotExist:
        return _error(f"Player '{name}' not found.", status=404)

    overall = player.scores.aggregate(
        total_games=Count("id"),
        best_score=Max("points"),
        average_score=Avg("points"),
        last_played=Max("created_at"),
    )
    if overall["average_score"] is not None:
        overall["average_score"] = round(overall["average_score"], 1)

    per_game = list(
        player.scores.values("game")
        .annotate(best_score=Max("points"), plays=Count("id"))
        .order_by("-best_score", "game")
    )
    for entry in per_game:
        entry["rank"] = _rank_of(entry["game"], entry["best_score"])

    return JsonResponse(
        {
            "player": player.name,
            "member_since": player.created_at,
            **overall,
            "games": per_game,
        }
    )


@require_GET
def stats(request):
    totals = Score.objects.aggregate(
        total_scores=Count("id"),
        average_score=Avg("points"),
        highest_score=Max("points"),
    )
    if totals["average_score"] is not None:
        totals["average_score"] = round(totals["average_score"], 1)

    record = Score.objects.select_related("player").order_by("-points", "created_at").first()
    games = list(
        Score.objects.values("game")
        .annotate(
            plays=Count("id"),
            players=Count("player", distinct=True),
            top_score=Max("points"),
        )
        .order_by("-plays", "game")
    )
    return JsonResponse(
        {
            "total_players": Player.objects.count(),
            **totals,
            "record_holder": (
                {"player": record.player.name, "game": record.game, "points": record.points}
                if record
                else None
            ),
            "games": games,
        }
    )
