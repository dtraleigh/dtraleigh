from django.urls import path

from parcels import views as parcels_views
from parcels.views import ParcelHistoryView

urlpatterns = [
    path("", parcels_views.main),
  ]
