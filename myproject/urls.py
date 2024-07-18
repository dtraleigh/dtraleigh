from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from develop import views as develop_views
from buildings import views as buildings_views
from newBernTOD import views as newbern_views

urlpatterns = [
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("admin/", admin.site.urls),
    path("eats/", include("eats.urls")),
    path("rpd/", include("rpd.urls")),
    path("itb/", develop_views.itb),
    path("ncod/", develop_views.ncod),
    path("dx/", develop_views.dx_zoning),
    path("dx40/", develop_views.dx_zoning40),
    path("tod/", newbern_views.tod),
    path("buildings/", buildings_views.building_date_map),
    path("buildings/geojson/<str:decade>/", buildings_views.geojson_helper),
    path("buildings/<str:decade>/", buildings_views.decade_map),
    path("buildings-chart/", buildings_views.bar_chart),
    path("lv-chart/", buildings_views.bar_chart2),
    path("lv-map-test/", buildings_views.land_value_test),
    path("lv-map/", buildings_views.land_value),
    path("new_bern_main/", newbern_views.new_bern_main),
    path("filter_tod/", newbern_views.filter_tod),
    path("tod/", include("newBernTOD.urls")),
    path("parcels/", include("parcels.urls")),
    path("parking/", include("parking.urls")),
  ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
