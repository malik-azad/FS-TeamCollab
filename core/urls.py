# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing_page_view, name='landing_page'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pending-verification/', views.pending_verification_view, name='pending_verification'),
    
    # --- Dashboard URLs ---
    path('dashboard/student/', views.student_dashboard_view, name='student_dashboard'),
    # Coordinator URLs are now split into multiple pages
    path('dashboard/coordinator/', views.coordinator_dashboard_view, name='coordinator_dashboard'), # This is the "Overview"
    path('dashboard/coordinator/students/', views.manage_students_view, name='manage_students'), # NEW
    path('dashboard/coordinator/feedback/', views.view_department_feedback_view, name='view_department_feedback'), # NEW
     path('dashboard/coordinator/analytics/', views.analytics_view, name='analytics'),

    # --- Feedback URLs ---
    path('feedback/give/', views.give_feedback_view, name='give_feedback'),
    path('feedback/<int:feedback_id>/view/', views.view_feedback_detail, name='view_feedback_detail'),
    path('feedback/<int:feedback_id>/delete/', views.delete_feedback_view, name='delete_feedback'),
    path('feedback/<int:feedback_id>/revoke-anonymity/', views.revoke_anonymity_view, name='revoke_anonymity'),
    
    # --- Profile & User Management URLs ---
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('coordinator/approve/<int:student_id>/', views.approve_student_view, name='approve_student'),
    path('coordinator/reject/<int:student_id>/', views.reject_student_view, name='reject_student'),
   
    # --- NEW URL FOR AI SUMMARIZATION ---
    path('coordinator/feedback/summarize/', views.summarize_feedback_view, name='summarize_feedback'),

]