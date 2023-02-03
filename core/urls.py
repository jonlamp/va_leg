from . import views
from django.urls import path, include

urlpatterns = [
    path("", view=views.index, name="index"),
    path("bill/<int:bill_id>",view=views.bill_view,name="bill_view"),
    path("search", view=views.search, name='search'),
    path("browse",view=views.browse,name="browse"),
    path("about",view=views.about, name="about"),
    path("user/", include('django.contrib.auth.urls')),
]