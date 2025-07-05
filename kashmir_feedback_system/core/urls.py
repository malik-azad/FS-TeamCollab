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
    path('dashboard/coordinator/', views.coordinator_dashboard_view, name='coordinator_dashboard'), # NEW URL
    # TODO: path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),

    path('feedback/give/', views.give_feedback_view, name='give_feedback'),
    path('feedback/<int:feedback_id>/view/', views.view_feedback_detail, name='view_feedback_detail'),
    path('feedback/<int:feedback_id>/delete/', views.delete_feedback_view, name='delete_feedback'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'), # NEW URL FOR EDIT PROFILE

    # TODO: Add URL for editing feedback if ever introduced
    # path('feedback/<int:feedback_id>/edit/', views.edit_feedback_view, name='edit_feedback'),
]