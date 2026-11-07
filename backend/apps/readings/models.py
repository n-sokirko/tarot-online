"""Reading session models. Owned by database-agent."""
from django.conf import settings
from django.db import models


class Reading(models.Model):
    LOCALE_CHOICES = [('ru', 'Russian'), ('en', 'English')]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='readings',
    )
    spread_type = models.ForeignKey('tarot.SpreadType', on_delete=models.PROTECT)
    question = models.TextField()
    locale = models.CharField(max_length=2, choices=LOCALE_CHOICES, default='ru')
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['-created_at']), models.Index(fields=['user', '-created_at'])]


class ReadingCard(models.Model):
    reading = models.ForeignKey(Reading, on_delete=models.CASCADE, related_name='cards')
    card = models.ForeignKey('tarot.Card', on_delete=models.PROTECT)
    position_index = models.PositiveSmallIntegerField()
    is_reversed = models.BooleanField(default=False)

    # Where the card sits on the free table, as a fraction of the surface
    # (0..1 from the top-left), so the layout survives a reload and renders the
    # same on any screen size. Fixed spreads ignore these and lay themselves out
    # from position_index; 0.5/0.5 just means "not placed by hand".
    x = models.FloatField(default=0.5)
    y = models.FloatField(default=0.5)

    class Meta:
        unique_together = ('reading', 'position_index')


class Interpretation(models.Model):
    reading = models.OneToOneField(Reading, on_delete=models.CASCADE, related_name='interpretation')
    body_md = models.TextField()
    model_used = models.CharField(max_length=64)
    prompt_version = models.CharField(max_length=32)
    generated_at = models.DateTimeField(auto_now_add=True)
    token_count = models.PositiveIntegerField(default=0)
    # One-line gist the model writes in a hidden tail (<memo>…</memo>): question,
    # cards, the takeaway. Fed back into later readings as the person's history.
    memo = models.CharField(max_length=300, blank=True)


class TarotProfile(models.Model):
    """How the tarologist talks to this person and what it remembers about them.

    Personas and style mirroring are Premium; the reading memory (memos of past
    readings) and the dossier work for every signed-in user who keeps memory on.
    """
    PERSONA_CLASSIC = 'classic'
    PERSONA_MIRA = 'mira'
    PERSONA_VAL = 'val'
    PERSONA_VAL18 = 'val18'
    PERSONA_AGATA = 'agata'
    PERSONA_CHOICES = [
        (PERSONA_CLASSIC, 'Classic'),
        (PERSONA_MIRA, 'Mira — warm'),
        (PERSONA_VAL, 'Val — bold'),
        (PERSONA_VAL18, 'Val 18+ — uncensored'),
        (PERSONA_AGATA, 'Agata — mystic'),
    ]
    DOSSIER_MAX_ITEMS = 12
    DOSSIER_MAX_LEN = 200

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='tarot_profile')
    persona = models.CharField(max_length=16, choices=PERSONA_CHOICES, default=PERSONA_CLASSIC)
    mirror_style = models.BooleanField(default=False)
    remember = models.BooleanField(default=True)
    adult_confirmed_at = models.DateTimeField(null=True, blank=True)
    # Short facts the tarologist keeps about the person: names, ongoing stories,
    # how they like to be spoken to, running jokes. A list of strings.
    dossier = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'TarotProfile({self.user_id}, {self.persona})'
