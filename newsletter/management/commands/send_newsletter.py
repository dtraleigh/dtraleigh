import logging
from datetime import timedelta

import feedparser
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.html import strip_tags

from newsletter.email import send_newsletter
from newsletter.models import SentPost

logger = logging.getLogger(__name__)

FEED_URL = "https://dtraleigh.com/feed/"
RETRY_CUTOFF_HOURS = 24


class Command(BaseCommand):
    help = "Poll the DTRaleigh RSS feed and send newsletters for new posts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed",
            action="store_true",
            help="Mark all current feed entries as already sent without emailing anyone.",
        )

    def handle(self, *args, **options):
        feed = feedparser.parse(FEED_URL)

        if feed.bozo and not feed.entries:
            self.stderr.write(f"Failed to parse RSS feed: {feed.bozo_exception}")
            return

        if options["seed"]:
            self._seed(feed)
            return

        self._send_new_posts(feed)

    def _seed(self, feed):
        created_count = 0
        for entry in feed.entries:
            guid = self._get_guid(entry)
            _, created = SentPost.objects.get_or_create(
                guid=guid,
                defaults={"title": entry.get("title", ""), "recipient_count": 0},
            )
            if created:
                created_count += 1

        self.stdout.write(f"Seeded {created_count} posts (skipped {len(feed.entries) - created_count} already existing).")

    def _send_new_posts(self, feed):
        new_entries = []
        retry_posts = {}

        cutoff = timezone.now() - timedelta(hours=RETRY_CUTOFF_HOURS)

        for entry in feed.entries:
            guid = self._get_guid(entry)
            try:
                sent_post = SentPost.objects.get(guid=guid)
                if sent_post.recipient_count == 0:
                    if sent_post.sent_at >= cutoff:
                        # Failed previous attempt within cutoff — retry
                        retry_posts[guid] = sent_post
                        new_entries.append(entry)
                    else:
                        # Exceeded retry cutoff — abandon
                        logger.warning(
                            "Abandoning newsletter for '%s' (guid=%s) after %d hours with 0 recipients.",
                            sent_post.title, guid, RETRY_CUTOFF_HOURS,
                        )
            except SentPost.DoesNotExist:
                new_entries.append(entry)

        if not new_entries:
            self.stdout.write("No new posts found.")
            return

        # Sort oldest first by published date
        new_entries.sort(key=lambda e: e.get("published_parsed") or ())

        # Respect NEWSLETTER_SEND_ALL_NEW setting
        if not getattr(settings, "NEWSLETTER_SEND_ALL_NEW", True):
            new_entries = [new_entries[-1]]

        for entry in new_entries:
            guid = self._get_guid(entry)
            title = entry.get("title", "Untitled")
            html_content = self._get_html_content(entry)
            text_content = strip_tags(html_content)
            post_url = entry.get("link", "")

            # Create or retrieve SentPost before sending (idempotency guard)
            sent_post = retry_posts.get(guid)
            if sent_post is None:
                sent_post = SentPost.objects.create(
                    guid=guid, title=title, recipient_count=0
                )

            self.stdout.write(f"Sending newsletter for: {title}")
            count = send_newsletter(title, html_content, text_content, post_url, sent_post)

            sent_post.recipient_count = count
            sent_post.save(update_fields=["recipient_count"])
            self.stdout.write(f"  Sent to {count} subscribers.")

    def _get_guid(self, entry):
        return entry.get("id") or entry.get("link", "")

    def _get_html_content(self, entry):
        # feedparser stores content:encoded in entry.content
        if hasattr(entry, "content") and entry.content:
            return entry.content[0].get("value", "")
        return entry.get("summary", "")
