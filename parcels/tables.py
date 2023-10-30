import django_tables2 as tables
from parcels.models import Parcel


class ParcelHistoryTable(tables.Table):
    class Meta:
        model = Parcel
        template_name = "django_tables2/bootstrap.html"
        fields = ("modified_date", )
