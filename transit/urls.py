from django.urls import path

from transit import views as transit_views

urlpatterns = [
    path("", transit_views.main),
    path("high-frequency/<day_of_the_week>", transit_views.high_frequency),
    path("high-frequency/hours/<day_of_the_week>", transit_views.high_frequency_chart)
  ]
