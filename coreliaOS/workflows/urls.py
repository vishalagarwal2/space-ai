from django.urls import path
from . import views

app_name = 'workflows'

urlpatterns = [
    path('test/', views.helloworld, name='helloworld'),
    path('marketing/', views.marketing_workflow, name='marketing_workflow'),
]