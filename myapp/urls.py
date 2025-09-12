from django.urls import path
from . import views

urlpatterns = [
    path('', views.new_chat_session, name='new_chat'),
    path('chat/<uuid:session_id>/', views.chat_view, name='chat_view'),
    path('get_response/', views.get_response, name='get_response'),
    # NEW: Endpoint for fetching suggested prompts
    path('get_suggestions/', views.get_suggestions, name='get_suggestions'),
]