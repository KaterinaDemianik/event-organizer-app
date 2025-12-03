from django.urls import path
from .views import (
    LoginView,
    SignupView,
    ProfileView,
    admin_create_user,
    UserPasswordChangeView,
    UserPasswordChangeDoneView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("password/change/", UserPasswordChangeView.as_view(), name="password_change"),
    path("password/change/done/", UserPasswordChangeDoneView.as_view(), name="password_change_done"),
    path("admin/create-user/", admin_create_user, name="admin_create_user"),
]