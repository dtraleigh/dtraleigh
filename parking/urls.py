from django.urls import path

from parking import views as parking_views

urlpatterns = [
    path("", parking_views.main),
  ]
