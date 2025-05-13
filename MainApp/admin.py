from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Event)
admin.site.register(TicketType)
admin.site.register(TicketSale)
admin.site.register(BankAccount)
admin.site.register(EventFace)
admin.site.register(EventHighlight)
admin.site.register(UserAvatar)
admin.site.register(Order)
admin.site.register(OrderItem)