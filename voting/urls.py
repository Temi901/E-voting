from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vote/<int:election_id>/', views.vote_view, name='vote'),
    path('results/<int:election_id>/', views.results_view, name='results'),
    path('results/<int:election_id>/export/pdf/', views.export_results_pdf, name='export_results_pdf'),
    path('results/<int:election_id>/export/excel/', views.export_results_excel, name='export_results_excel'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
