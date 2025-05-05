from django.urls import path
from .views import (CustomLoginView, LogoutView, ProfileView,
                    RegisterView, PasswordResetRequestView, PasswordResetConfirmView, 
                    LanguageSettingView, AccountDeleteView)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('register/', RegisterView.as_view(), name='register'),
    path('reset-password/', PasswordResetRequestView.as_view(), name='reset-password'),
    path('reset-password-confirm/', PasswordResetConfirmView.as_view(), name='reset-password-confirm'),
    path('settings/language/', LanguageSettingView.as_view(), name='language-setting'),
    path('account/delete/', AccountDeleteView.as_view(), name='account-delete')
]
