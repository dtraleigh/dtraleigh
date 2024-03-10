from django.urls import path

from parcels import views as parcels_views
from parcels.views import ParcelHistoryView

urlpatterns = [
    path("", parcels_views.main),
    path("debug/<int:parcel_id>/<int:subsection_id>/", parcels_views.debug)
  ]
