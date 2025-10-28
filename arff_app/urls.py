
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_arff, name='upload_arff'),
    path('api/upload/', views.api_upload_arff, name='api_upload_arff'),
]
