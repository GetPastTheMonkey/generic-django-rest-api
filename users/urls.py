from django.urls import path

from users import views

urlpatterns = [
    # User Management
    path("login", views.login),
    path("logout", views.logout),
    path("change-password", views.change_password),
    path("change-email-address", views.change_email_address),
    path("change-phone-number", views.change_phone_number),
    path("signup", views.signup),
    path("reset-password", views.reset_password),

    # User Data
    path("me", views.MeView.as_view()),
    path("<uuid:user_id>", views.user_by_id),
]
