from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from parcels import views as parcels_views

urlpatterns = [
    path("", parcels_views.main),
  ]
