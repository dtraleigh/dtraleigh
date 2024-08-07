from django.urls import path

from parcels import views as parcels_views
from parcels.views import ParcelHistoryView

urlpatterns = [
    path("", parcels_views.main),
    path("history/", parcels_views.history),
    path("debug/<int:parcel_id>/<int:subsection_id>/", parcels_views.debug),
    path("debug/raleigh_map/", parcels_views.raleigh_map)
  ]
