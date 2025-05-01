from django.urls import path
from .views import MouvementListView, MouvementCreateView

app_name = 'stocks'
urlpatterns = [
    path('',           MouvementListView.as_view(), name='mouvements'),
    path('nouveau/',   MouvementCreateView.as_view(), name='mouvement_create'),
]