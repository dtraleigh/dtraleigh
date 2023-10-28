from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from newBernTOD import views as newbern_views

urlpatterns = [
    path("", newbern_views.tod),
    path("show_all_parcels/", newbern_views.show_all_parcels),
    path("ncod/<int:ncod_id>/", newbern_views.show_ncod_by_id),
    path("ncod/<str:ncod_name>/", newbern_views.show_ncod_by_name),
    path("hod/<str:hod_name>/", newbern_views.show_hod_by_name),
    path("ncod/parcels/<int:ncod_id>/", newbern_views.show_all_parcels_in_ncod),
  ]
