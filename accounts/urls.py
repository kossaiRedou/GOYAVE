from django.urls import path
from .views import (
    LoginView, LogoutView,
    TeamListView, TeamCreateView, TeamUpdateView, TeamToggleStatusView,
    UserActionListView, ProfileView
)
from django.contrib.auth import views as auth_views

app_name = 'accounts'
urlpatterns = [
    # Auth
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
    # Team
    path('team/', TeamListView.as_view(), name='team_list'),
    path('team/add/', TeamCreateView.as_view(), name='team_add'),
    path('team/<int:pk>/edit/', TeamUpdateView.as_view(), name='team_edit'),
    path('team/<int:pk>/toggle-status/', TeamToggleStatusView.as_view(), name='team_toggle_status'),
    # Actions
    path('actions/', UserActionListView.as_view(), name='user_actions'),
]
