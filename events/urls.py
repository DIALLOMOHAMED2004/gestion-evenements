from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create_event, name='create_event'),
    path('list/', views.event_list, name='event_list'),
    path('<int:event_id>/', views.event_detail, name='event_detail'),
    path('<int:event_id>/invite/<str:invitation_link>/', views.event_detail, name='event_detail_invite'),
    path('<int:event_id>/register/', views.event_register, name='event_register'),
    path('<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('<int:event_id>/delete/', views.delete_event, name='delete_event'),
]
