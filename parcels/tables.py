import django_tables2 as tables
from parcels.models import Parcel


class ParcelHistoryTable(tables.Table):
    modified_date = tables.DateTimeColumn(format="M d, Y")

    class Meta:
        model = Parcel
        attrs = {"class": "table table-bordered table-hover table-sm table-responsive"}
        template_name = "django_tables2/bootstrap.html"
        fields = ("modified_date",)
