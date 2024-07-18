from django.urls import path

from parking import views as parking_views

urlpatterns = [
    path("", parking_views.main),
    path("<day_of_the_week>", parking_views.main),
  ]
