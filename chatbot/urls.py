from django.urls import path
from . import views

urlpatterns=[
    path('', views.chatbot, name='chatbot'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
    path('sentiments', views.view_sentiments, name='view_sentiments' ),
    path('overallsentiments', views.overall_sentiment_score, name='overall_sentiment_score' )
]