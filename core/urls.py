from . import views
from django.urls import path, include

urlpatterns = [
    path("", view=views.index, name="index"),
    path("bill/<int:bill_id>",view=views.bill_view,name="bill_view")
]