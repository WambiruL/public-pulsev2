from django.urls import include, path
from . import views

urlpatterns=[
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('chatbot/', include('chatbot.urls')),
]