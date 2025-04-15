from django.core.management.base import BaseCommand
from develop.models import Subscriber
from develop.management.commands.actions import ensure_correct_discourse_title


class Command(BaseCommand):
    help = "Ensure a Discourse topic has the correct title"

    def handle(self, *args, **options):
        try:
            subscriber = Subscriber.objects.get(id=2)
            ensure_correct_discourse_title(subscriber)
            self.stdout.write(self.style.SUCCESS("Title check completed."))
        except Subscriber.DoesNotExist:
            self.stderr.write(self.style.ERROR("Subscriber with ID 2 does not exist."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))
