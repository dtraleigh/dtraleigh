from django.urls import path

from rpd import views

urlpatterns = [
    path("glenwood/", views.glenwood),
    path("glenwood/map", views.glenwood_map),
    path("glenwood_test", views. glenwood_test),
]
