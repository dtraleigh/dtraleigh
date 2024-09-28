from django.urls import path

from transit import views as transit_views

urlpatterns = [
    path("", transit_views.main),
  ]
