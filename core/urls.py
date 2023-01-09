from . import views
from django.urls import path, include

urlpatterns = [
    path("", view=views.index, name="index")
]