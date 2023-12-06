from django.core.management.base import BaseCommand
from django.db.models import Count
from parcels.models import Parcel


class Command(BaseCommand):
    def handle(self, *args, **options):
        dupes_value_set = Parcel.objects.values('objectid').annotate(Count('id')).order_by().filter(id__count__gt=1)
        dupes = Parcel.objects.filter(objectid__in=[item['objectid'] for item in dupes_value_set])
        print(f"There are {len(dupes_value_set)} parcel instances with the same objectid.")

        num_dupes = {"2 dupes": 0, "3 dupes": 0, "More dupes": 0}
        for dupe in dupes_value_set:
            if dupe["id__count"] == 2:
                num_dupes["2 dupes"] += 1
            elif dupe["id__count"] == 3:
                num_dupes["3 dupes"] += 1
            elif dupe["id__count"] > 3:
                num_dupes["More dupes"] += 1
        print(f"dupe breakdown is {num_dupes}")

        # date_of_dupe_creation = []
        # for count, dupe in enumerate(dupes):
        #     print(f"Checking dupe {count}")
        #     date_of_dupe_creation.append(dupe.created_date.date())
        # print(f"Dates spanning dupe creation. {list(set(date_of_dupe_creation))}")

        # Since all dupes are on the same date, the most recent scan, I'm taking the 'delete all and try again approach'
        for count, dupe in enumerate(dupes):
            print(f"Deleting dupe {count}, {dupe}")
            dupe.delete()
