from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static

from develop import views as develop_views
from buildings import views as buildings_views
from newBernTOD import views as newbern_views

urlpatterns = [
                  path("admin/", admin.site.urls),
                  path("itb/", develop_views.itb),
                  path("ncod/", develop_views.ncod),
                  path("dx/", develop_views.dx_zoning),
                  path("dx40/", develop_views.dx_zoning40),
                  path("tod", newbern_views.tod),
                  path("filter_tod", newbern_views.filter_tod),
                  path("tod/show_all_parcels", newbern_views.show_all_parcels),
                  path("tod/ncod/<int:ncod_id>", newbern_views.show_ncod_by_id),
                  path("tod/ncod/<str:ncod_name>", newbern_views.show_ncod_by_name),
                  path("tod/ncod/parcels/<int:ncod_id>", newbern_views.show_all_parcels_in_ncod),
                  path("new_bern_main", newbern_views.new_bern_main),
                  path("buildings/", buildings_views.building_date_map),
                  path("buildings/geojson/<str:decade>/", buildings_views.geojson_helper),
                  path("buildings/<str:decade>/", buildings_views.decade_map),
                  path("buildings-chart/", buildings_views.bar_chart),
                  path("lv-chart/", buildings_views.bar_chart2),
                  path("lv-map-test/", buildings_views.land_value_test),
                  path("lv-map/", buildings_views.land_value)
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
