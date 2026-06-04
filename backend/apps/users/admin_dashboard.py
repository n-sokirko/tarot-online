"""Staff-only analytics dashboard with charts (Chart.js)."""
import datetime
import json

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone

User = get_user_model()
DAYS = 14


def _series(qs, date_field, days=DAYS):
    today = timezone.localdate()
    start = today - datetime.timedelta(days=days - 1)
    rows = (
        qs.filter(**{f'{date_field}__date__gte': start})
        .annotate(d=TruncDate(date_field))
        .values('d')
        .annotate(c=Count('id'))
    )
    by = {r['d']: r['c'] for r in rows}
    labels, data = [], []
    for i in range(days):
        day = start + datetime.timedelta(days=i)
        labels.append(day.strftime('%d.%m'))
        data.append(by.get(day, 0))
    return labels, data


@staff_member_required
def dashboard(request):
    from apps.billing.models import Subscription, UsageLedger
    from apps.readings.models import Reading
    from apps.telegram_bot.models import TelegramUser

    week_ago = timezone.now() - datetime.timedelta(days=7)

    cards = {
        'Пользователей': User.objects.count(),
        'Новых за 7 дней': User.objects.filter(date_joined__gte=week_ago).count(),
        'Раскладов всего': Reading.objects.count(),
        'Раскладов за 7 дней': Reading.objects.filter(created_at__gte=week_ago).count(),
        'Telegram-юзеров': TelegramUser.objects.count(),
        'Подписаны на пуш': TelegramUser.objects.filter(daily_push=True).count(),
        'Активный Premium': Subscription.objects.filter(status='active').count(),
        'AI-генераций': UsageLedger.objects.filter(cost_credits__gt=0).count(),
    }

    u_labels, u_data = _series(User.objects.all(), 'date_joined')
    r_labels, r_data = _series(Reading.objects.all(), 'created_at')

    spreads = list(
        Reading.objects.values('spread_type__slug').annotate(c=Count('id')).order_by('-c')
    )
    sp_labels = [s['spread_type__slug'] or '—' for s in spreads]
    sp_data = [s['c'] for s in spreads]

    ctx = {
        'u_labels': u_labels, 'u_data': u_data,
        'r_labels': r_labels, 'r_data': r_data,
        'sp_labels': sp_labels, 'sp_data': sp_data,
    }
    cards_html = ''.join(
        f'<div class="card"><div class="num">{v}</div><div class="lbl">{k}</div></div>'
        for k, v in cards.items()
    )

    html = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<title>Дашборд · Tarot Online</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  body{{margin:0;background:#0b0b1f;color:#e6e1f5;font-family:system-ui,sans-serif;padding:24px}}
  h1{{color:#d4af37;font-weight:500}} a{{color:#d4af37}}
  .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:20px 0}}
  .card{{background:rgba(212,175,55,0.06);border:1px solid rgba(212,175,55,0.25);border-radius:14px;padding:18px}}
  .num{{font-size:2rem;color:#d4af37;font-weight:600}} .lbl{{font-size:.8rem;opacity:.7;margin-top:4px}}
  .charts{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px}}
  .chart{{background:rgba(212,175,55,0.04);border:1px solid rgba(212,175,55,0.18);border-radius:14px;padding:18px}}
  @media(max-width:800px){{.charts{{grid-template-columns:1fr}}}}
</style></head><body>
<h1>✦ Дашборд Tarot Online</h1>
<a href="/admin/">← в админку</a>
<div class="cards">{cards_html}</div>
<div class="charts">
  <div class="chart"><h3>Новые пользователи (14 дней)</h3><canvas id="users"></canvas></div>
  <div class="chart"><h3>Расклады (14 дней)</h3><canvas id="readings"></canvas></div>
  <div class="chart"><h3>Популярность раскладов</h3><canvas id="spreads"></canvas></div>
</div>
<script>
const D={json.dumps(ctx)};
const gold='#d4af37', grid='rgba(212,175,55,0.12)';
const opt={{plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{color:grid}},ticks:{{color:'#9a93b8'}}}},y:{{grid:{{color:grid}},ticks:{{color:'#9a93b8'}},beginAtZero:true}}}}}};
new Chart(users,{{type:'line',data:{{labels:D.u_labels,datasets:[{{data:D.u_data,borderColor:gold,backgroundColor:'rgba(212,175,55,0.15)',fill:true,tension:0.35}}]}},options:opt}});
new Chart(readings,{{type:'bar',data:{{labels:D.r_labels,datasets:[{{data:D.r_data,backgroundColor:'rgba(168,196,234,0.6)'}}]}},options:opt}});
new Chart(spreads,{{type:'doughnut',data:{{labels:D.sp_labels,datasets:[{{data:D.sp_data,backgroundColor:['#d4af37','#a8c4ea','#9ad9a0','#e8915a','#c9a4d8']}}]}},options:{{plugins:{{legend:{{labels:{{color:'#e6e1f5'}}}}}}}}}});
</script></body></html>"""
    return HttpResponse(html)
