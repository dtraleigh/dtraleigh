import html
import logging

import feedparser
from django.core.management.base import BaseCommand, CommandError
from django.utils.html import strip_tags

from newsletter.email import send_newsletter
from newsletter.management.commands.send_newsletter import (
    FEED_URL,
    Command as SendNewsletterCommand,
)
from newsletter.models import SendLog, SentPost

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Resend a previously-sent newsletter. Re-fetches the post from the "
        "RSS feed so any edits are picked up. Use sparingly."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "guid",
            help="The guid of the post to resend (e.g. 'https://dtraleigh.com/?p=12597').",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip the confirmation prompt.",
        )

    def handle(self, *args, **options):
        guid = options["guid"]

        try:
            sent_post = SentPost.objects.get(guid=guid)
        except SentPost.DoesNotExist:
            raise CommandError(f"No SentPost found with guid '{guid}'.")

        feed = feedparser.parse(FEED_URL)
        if feed.bozo and not feed.entries:
            raise CommandError(f"Failed to parse RSS feed: {feed.bozo_exception}")

        helper = SendNewsletterCommand()
        entry = next(
            (e for e in feed.entries if helper._get_guid(e) == guid),
            None,
        )
        if entry is None:
            raise CommandError(
                f"Post with guid '{guid}' not found in current RSS feed. "
                "Cannot resend a post that is no longer published."
            )

        title = entry.get("title", "Untitled")
        full_html = helper._get_html_content(entry)
        html_content = helper._get_preview_content(full_html)
        text_content = html.unescape(strip_tags(html_content))
        post_url = entry.get("link", "")
        subject = f"DTRaleigh: {title}"

        self.stdout.write(f"About to resend newsletter:")
        self.stdout.write(f"  Title: {title}")
        self.stdout.write(f"  Guid:  {guid}")
        self.stdout.write(f"  Originally sent: {sent_post.sent_at}")
        self.stdout.write(f"  Original recipient count: {sent_post.recipient_count}")

        if not options["yes"]:
            answer = input("Send this newsletter to all confirmed subscribers? [y/N]: ")
            if answer.strip().lower() not in ("y", "yes"):
                self.stdout.write("Aborted.")
                return

        self.stdout.write(f"Resending newsletter for: {title}")
        count = send_newsletter(subject, html_content, text_content, post_url, sent_post)

        SendLog.objects.create(
            sent_post=sent_post,
            event_type=SendLog.EVENT_NEWSLETTER_SENT,
            detail=f"Resend to {count} subscribers (originally {sent_post.recipient_count}).",
        )
        sent_post.recipient_count = count
        sent_post.save(update_fields=["recipient_count"])
        self.stdout.write(f"  Resent to {count} subscribers.")
