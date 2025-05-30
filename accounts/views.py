from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth import views as auth_views
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import User, UserAction
from .forms import CustomUserCreationForm, CustomUserChangeForm

class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'MANAGER'

# Team management
class TeamListView(ManagerRequiredMixin, ListView):
    model = User
    template_name = 'accounts/team_list.html'
    context_object_name = 'employees'
    queryset = User.objects.filter(role='EMPLOYEE')

class TeamCreateView(ManagerRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/team_form.html'
    success_url = reverse_lazy('accounts:team_list')

    def form_valid(self, form):
        form.instance.role = 'EMPLOYEE'
        response = super().form_valid(form)
        messages.success(self.request, f"L'employé {form.instance.username} a été créé avec succès.")
        return response

class TeamUpdateView(ManagerRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'accounts/team_form.html'
    success_url = reverse_lazy('accounts:team_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Les informations de {form.instance.username} ont été mises à jour.")
        return response

class TeamToggleStatusView(ManagerRequiredMixin, UpdateView):
    model = User
    fields = ['is_active']
    http_method_names = ['post']
    success_url = reverse_lazy('accounts:team_list')

    def form_valid(self, form):
        user = form.instance
        user.is_active = not user.is_active
        response = super().form_valid(form)
        status = "activé" if user.is_active else "désactivé"
        messages.success(self.request, f"L'employé {user.username} a été {status} avec succès.")
        return response

# Auth views reuse Django
class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'

class LogoutView(auth_views.LogoutView):
    template_name = 'accounts/logout.html'

class UserActionListView(ManagerRequiredMixin, ListView):
    model = UserAction
    template_name = 'accounts/user_actions.html'
    context_object_name = 'actions'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filtres
        user_id = self.request.GET.get('user')
        action_type = self.request.GET.get('type')
        date_from = self.request.GET.get('from')
        date_to = self.request.GET.get('to')

        if user_id:
            qs = qs.filter(user_id=user_id)
        if action_type:
            qs = qs.filter(action_type=action_type)
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        context['action_types'] = UserAction.ACTION_TYPES
        return context

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

