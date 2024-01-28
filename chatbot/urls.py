from django.urls import path
from . import views

urlpatterns=[
    path('chatpulse', views.chatbot, name='chatbot'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout')
]