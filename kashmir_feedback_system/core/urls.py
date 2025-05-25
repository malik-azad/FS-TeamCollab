# core/urls.py
from django.urls import path
from . import views

app_name = 'core' # Namespace for URLs

urlpatterns = [
    path('', views.landing_page_view, name='landing_page'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('dashboard/student/', views.student_dashboard_view, name='student_dashboard'),
    # TODO: Add URLs for coordinator and admin dashboards later
    # path('dashboard/coordinator/', views.coordinator_dashboard_view, name='coordinator_dashboard'),
    # path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),

    path('feedback/give/', views.give_feedback_view, name='give_feedback'),
    
    
    # TODO: Add URLs for editing and deleting feedback later
    # path('feedback/edit/<int:feedback_id>/', views.edit_feedback_view, name='edit_feedback'),
    # path('feedback/delete/<int:feedback_id>/', views.delete_feedback_view, name='delete_feedback'),
]