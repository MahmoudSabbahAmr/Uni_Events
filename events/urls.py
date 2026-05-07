from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('events/', views.events_list),
    path('event/<int:id>/', views.event_detail),
    path('book/<int:id>/', views.book_event),
    path('my-tickets/', views.my_tickets),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('cancel/<int:id>/', views.cancel_booking),
    path('register/', views.register_view),
    # REST API endpoints
    path('api/events/', views.api_events),
    path('api/events/<int:id>/', views.api_event_detail),
    path('api/book/<int:id>/', views.api_book_event),
    path('api/my-bookings/', views.api_my_bookings),
]