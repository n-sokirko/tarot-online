"""Contest models — referral giveaway for channel-subscriber growth.

The flow:
  - Admin creates a Contest (channel, dates, prize count/months, min_invites).
  - User runs /contest → ContestEntry row + personal channel invite link.
  - When someone joins the channel via that link, Telegram's chat_member update
    carries invite_link.name. The bot increments ContestInvite for the inviter.
  - At draw time, admin clicks an action; we randomly pick N winners from
    entries with invites_count >= min_invites whose invitees are still members.
"""
from django.db import models


class Contest(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_FINISHED = 'finished'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_ACTIVE, 'Активен'),
        (STATUS_FINISHED, 'Завершён'),
    ]

    title = models.CharField(max_length=120)
    # Channel handle bot will create invite links for. Bot must be admin there.
    channel = models.CharField(
        max_length=64,
        help_text='@username канала, например @tarro_bot_group',
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    prize_count = models.PositiveSmallIntegerField(default=10)
    prize_months = models.PositiveSmallIntegerField(default=1)
    prize_plan_slug = models.CharField(
        max_length=64, default='premium',
        help_text='Slug плана из billing.Plan, который выдаём победителям.',
    )

    min_invites = models.PositiveSmallIntegerField(
        default=3,
        help_text='Минимум приглашённых, чтобы попасть в жеребьёвку.',
    )

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    winners_drawn_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Конкурс'
        verbose_name_plural = 'Конкурсы'

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"


class ContestEntry(models.Model):
    """One participant in a contest. Holds their personal channel invite link."""
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='entries')
    tg_user = models.ForeignKey(
        'telegram_bot.TelegramUser',
        on_delete=models.CASCADE,
        related_name='contest_entries',
    )

    # Telegram invite link fields
    invite_link_url = models.URLField(max_length=255)
    # Telegram limits invite_link.name to 32 chars — we set 'contest:<entry_id>'.
    invite_link_name = models.CharField(max_length=32, unique=True)

    is_winner = models.BooleanField(default=False)
    prize_granted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['contest', 'tg_user'],
                name='uniq_contest_entry_per_user',
            ),
        ]
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'

    def __str__(self) -> str:
        return f"{self.tg_user} → {self.contest}"


class ContestInvite(models.Model):
    """One successful invite — somebody joined the channel via entry's link."""
    entry = models.ForeignKey(ContestEntry, on_delete=models.CASCADE, related_name='invites')
    # tg_id of the invited user
    invited_tg_id = models.BigIntegerField()
    joined_at = models.DateTimeField(auto_now_add=True)
    # Updated by the "verify before draw" sweep.
    still_member = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['entry', 'invited_tg_id'],
                name='uniq_invite_per_invited_per_entry',
            ),
        ]
        indexes = [models.Index(fields=['invited_tg_id'])]
        verbose_name = 'Приглашение'
        verbose_name_plural = 'Приглашения'

    def __str__(self) -> str:
        return f"{self.invited_tg_id} → {self.entry_id}"
