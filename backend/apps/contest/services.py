"""Contest business logic — kept pure (no telegram-bot framework) so it's
reusable from both bot handlers and admin actions."""
import logging
import random
from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.contest.models import Contest, ContestEntry, ContestInvite

log = logging.getLogger(__name__)


def active_contest(channel: Optional[str] = None) -> Optional[Contest]:
    """Return the currently active contest, optionally filtered by channel."""
    now = timezone.now()
    qs = Contest.objects.filter(
        status=Contest.STATUS_ACTIVE,
        starts_at__lte=now,
        ends_at__gt=now,
    )
    if channel:
        qs = qs.filter(channel=channel)
    return qs.first()


def _entry_name(entry_id: int) -> str:
    """Stable invite_link.name we attach to the personal Telegram invite link.
    Telegram caps invite_link.name at 32 chars."""
    return f"contest:{entry_id}"


@transaction.atomic
def get_or_create_entry(contest: Contest, tg_user) -> tuple[ContestEntry, bool]:
    """Return (entry, created). Caller is responsible for filling invite_link_*
    if created=True — see register_invite_link()."""
    try:
        return ContestEntry.objects.get(contest=contest, tg_user=tg_user), False
    except ContestEntry.DoesNotExist:
        pass

    entry = ContestEntry.objects.create(
        contest=contest,
        tg_user=tg_user,
        invite_link_url='',         # filled in register_invite_link()
        invite_link_name='',
    )
    entry.invite_link_name = _entry_name(entry.id)
    entry.save(update_fields=['invite_link_name'])
    return entry, True


def register_invite_link(entry: ContestEntry, url: str) -> None:
    """Save the actual Telegram invite link URL on a fresh entry."""
    entry.invite_link_url = url
    entry.save(update_fields=['invite_link_url'])


def record_invite(invite_link_name: str, invited_tg_id: int) -> Optional[ContestInvite]:
    """Called when chat_member fires with status=member and invite_link is ours.
    Idempotent: same (entry, invited_tg_id) can't be counted twice."""
    if not invite_link_name or not invite_link_name.startswith('contest:'):
        return None
    try:
        entry_id = int(invite_link_name.split(':', 1)[1])
    except (ValueError, IndexError):
        return None
    try:
        entry = ContestEntry.objects.select_related('contest').get(id=entry_id)
    except ContestEntry.DoesNotExist:
        return None
    if entry.contest.status != Contest.STATUS_ACTIVE:
        return None
    if entry.tg_user.tg_id == invited_tg_id:
        return None  # can't invite yourself

    invite, _ = ContestInvite.objects.get_or_create(
        entry=entry,
        invited_tg_id=invited_tg_id,
    )
    return invite


def leaderboard(contest: Contest, limit: int = 10):
    """Top entries by current invite count."""
    return (
        ContestEntry.objects
        .filter(contest=contest)
        .annotate(invites_count=Count('invites', filter=Q(invites__still_member=True)))
        .order_by('-invites_count', 'created_at')[:limit]
    )


def entry_stats(entry: ContestEntry) -> dict:
    """Per-user stats for the /contest reply."""
    qs = ContestEntry.objects.filter(contest=entry.contest).annotate(
        invites_count=Count('invites', filter=Q(invites__still_member=True))
    ).order_by('-invites_count', 'created_at')
    rank = 1
    my_count = 0
    for i, e in enumerate(qs, start=1):
        if e.id == entry.id:
            rank = i
            my_count = e.invites_count
            break
    total_participants = qs.count()
    return {
        'invites_count': my_count,
        'rank': rank,
        'total_participants': total_participants,
        'min_invites': entry.contest.min_invites,
    }


def draw_winners(contest: Contest) -> list[ContestEntry]:
    """Randomly pick prize_count winners from eligible entries.
    Idempotent — if winners were already drawn, returns them as-is."""
    already = list(contest.entries.filter(is_winner=True))
    if already:
        return already

    eligible = list(
        ContestEntry.objects
        .filter(contest=contest)
        .annotate(invites_count=Count('invites', filter=Q(invites__still_member=True)))
        .filter(invites_count__gte=contest.min_invites)
    )
    if not eligible:
        return []

    k = min(contest.prize_count, len(eligible))
    winners = random.sample(eligible, k)
    ContestEntry.objects.filter(id__in=[w.id for w in winners]).update(is_winner=True)
    contest.status = Contest.STATUS_FINISHED
    contest.winners_drawn_at = timezone.now()
    contest.save(update_fields=['status', 'winners_drawn_at'])
    return list(ContestEntry.objects.filter(id__in=[w.id for w in winners]))


def grant_prize(entry: ContestEntry) -> bool:
    """Activate premium for a winner. Idempotent by prize_granted_at.
    Returns True if granted now, False if already granted or no linked Django user."""
    if entry.prize_granted_at:
        return False
    if not entry.tg_user.user_id:
        log.warning("Contest winner entry %s has no Django user — can't grant prize.", entry.id)
        return False

    from apps.billing.models import Plan, Subscription, Entitlement
    from apps.billing.services import grant_credits

    try:
        plan = Plan.objects.get(slug=entry.contest.prize_plan_slug)
    except Plan.DoesNotExist:
        log.error("Contest %s: prize plan '%s' not found", entry.contest_id,
                  entry.contest.prize_plan_slug)
        return False

    period_end = timezone.now() + timedelta(days=30 * entry.contest.prize_months)

    with transaction.atomic():
        Subscription.objects.create(
            user=entry.tg_user.user,
            plan=plan,
            provider=Subscription.PROVIDER_TELEGRAM,
            tg_payment_charge_id=f'contest:{entry.id}',
            paddle_subscription_id=None,
            status=Subscription.STATUS_ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=period_end,
        )
        for key in plan.entitlement_keys or []:
            Entitlement.objects.update_or_create(
                user=entry.tg_user.user, key=key,
                defaults={'expires_at': period_end, 'source': f'contest:{entry.contest_id}'},
            )
        if plan.monthly_included_credits:
            grant_credits(
                user=entry.tg_user.user,
                amount=plan.monthly_included_credits,
                kind='subscription',
                reference_id=f'contest:{entry.id}',
            )
        entry.prize_granted_at = timezone.now()
        entry.save(update_fields=['prize_granted_at'])
    return True
