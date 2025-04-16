from django.urls import path
from .views import CustomLoginView, LogoutView, ProfileView
from .views import CustomLoginView, LogoutView, ProfileView, RegisterView


urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('register/', RegisterView.as_view(), name='register'),

]
