from django.db import models


class Player(models.Model):

    name = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Score(models.Model):
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="scores"
    )
    game = models.CharField(max_length=50, default="arcade")
    points = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["game", "-points"])]

    def __str__(self):
        return f"{self.player} - {self.game}: {self.points}"
