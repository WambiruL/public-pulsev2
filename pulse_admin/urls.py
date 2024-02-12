from django.urls import include, path
from . import views

urlpatterns=[
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),
    # path('chatbot/', include('chatbot.urls')),
    path('overall_sentiment_score', views.sentiment_analysis, name='sentiment_analysis' ),
    path('interaction_management', views.interaction_management, name='interaction_management'),

]