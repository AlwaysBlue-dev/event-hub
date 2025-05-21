from django.contrib import admin
from django.urls import path
from MainApp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.home, name='home'),
    path('category/<slug:slug>/', views.category_events, name='category_events'),
    path("login/", views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('user-profile/<str:username>/', views.userProfile, name='user-profile'),
    path('event/create/', views.create_event, name='create_event'),
    path("events/", views.events, name='events'),
    path('event-detail/<int:event_id>/', views.event_detail, name='event-detail'),
    path('event/<int:event_id>/buy/', views.buy_ticket, name='buy-ticket'),
    path("register/", views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:event_id>/', views.add_to_cart, name='add-to-cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove-from-cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete-event'),
    path('edit-event/<int:event_id>/', views.edit_event, name='edit-event'),
    path("ticket-purchase/", views.ticket_purchase, name='ticket_purchase'),
    path('purchase-ticket/', views.purchase_ticket, name='purchase-ticket'),
    path('validate-qr/', views.validate_qr, name='validate-qr'),
    path('event_sales/', views.event_sales, name='event-sales'),  # Overview of all events' sales
    path('event_sales/<int:event_id>/', views.event_sales_detail, name='event-sales-detail'),  # Detailed sales for specific event
    path('event-attendees/', views.event_attendees, name='event-attendees'),
    path('attendees/event/<int:event_id>/', views.event_attendee_stats, name='event_attendee_stats'),
    path('events/<int:event_id>/export/', views.export_event_sales_report, name='export_event_sales_report'),
    path('events/<int:event_id>/export_attendees/', views.export_event_attendees_report, name='export_event_attendees_report'),

]
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)