from django.contrib import admin
from .models import Event, EventRegistration,Category

admin.site.register(Event)
admin.site.register(EventRegistration)
admin.site.register(Category)
