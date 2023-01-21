from django.contrib import admin
from .models import Legislator, Session,Bill,Patron

# Register your models here.
admin.site.register(Session)
admin.site.register(Legislator)
admin.site.register(Bill)
admin.site.register(Patron)