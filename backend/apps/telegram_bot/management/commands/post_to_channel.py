"""
Management command: post_to_channel

Writes one fresh post for the public channel and publishes it. Run on a schedule
(Railway cron); replaces the fixed rotating pool in marketing/autopost.py, which
had cycled through its ~28 texts three times over.

    python manage.py post_to_channel --dry-run    # generate and print, send nothing
    python manage.py post_to_channel              # generate, publish, record
    python manage.py post_to_channel --kind promo # force the kind instead of rotating
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = 'Generate one non-repeating post and publish it to the Telegram channel.'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Print the post instead of publishing it. Nothing is written to the database, '
                 'so a dry run does not consume a topic.',
        )
        parser.add_argument(
            '--kind', choices=['fact', 'promo'], default=None,
            help='Force the post kind. Default rotates two facts to one promo.',
        )
        parser.add_argument(
            '--angle', default=None,
            help='Override the angle hint for a fact post (see channel.ANGLES).',
        )

    def handle(self, *args, **options) -> None:
        from apps.telegram_bot import channel
        from apps.telegram_bot.models import ChannelPost

        try:
            post = channel.generate(options['kind'], angle=options['angle'])
        except RuntimeError as exc:
            # Deliberately fatal: a gap in the schedule is better than a repeat,
            # and a non-zero exit makes the cron run show up as failed.
            raise CommandError(str(exc)) from exc

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN — {post.kind}, тема: {post.topic} '
                f'(попыток: {post.attempts}, модель: {post.model})'
            ))
            self.stdout.write('')
            self.stdout.write(post.text)
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('(не отправлено, в базу не записано)'))
            return

        row = ChannelPost.objects.create(
            kind=post.kind,
            topic=post.topic,
            text=post.text,
            fingerprint=channel.fingerprint(post.text),
            model_used=post.model,
            input_tokens=post.input_tokens,
            output_tokens=post.output_tokens,
            attempts=post.attempts,
        )

        try:
            message_id = channel.send_to_channel(post.text)
        except Exception as exc:  # noqa: BLE001 — recorded, then re-raised
            row.status = ChannelPost.STATUS_FAILED
            row.error = str(exc)[:2000]
            row.save(update_fields=['status', 'error'])
            raise CommandError(f'post generated but not sent: {exc}') from exc

        row.status = ChannelPost.STATUS_PUBLISHED
        row.published_at = timezone.now()
        row.tg_message_id = message_id
        row.save(update_fields=['status', 'published_at', 'tg_message_id'])

        self.stdout.write(self.style.SUCCESS(
            f'Опубликовано: [{post.kind}] {post.topic} '
            f'(message_id={message_id}, попыток: {post.attempts})'
        ))
