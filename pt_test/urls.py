from django.urls import path

from . import views

urlpatterns = [
    path(r'test_import', views.test_import, name='test_import'),
    path(r'handle_json', views.handle_json, name='handle_json'),
    path(r'test_post', views.test_post, name='test_post'),
    path(r'test_subprocess', views.test_subprocess, name='test_subprocess'),
]
