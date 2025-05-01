from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth import views as auth_views
from .models import User
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
        # Force role to EMPLOYEE
        form.instance.role = 'EMPLOYEE'
        return super().form_valid(form)

class TeamUpdateView(ManagerRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'accounts/team_form.html'
    success_url = reverse_lazy('accounts:team_list')

class TeamDeleteView(ManagerRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/team_confirm_delete.html'
    success_url = reverse_lazy('accounts:team_list')

# Auth views reuse Django
class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'

class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('accounts:login')

