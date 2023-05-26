from django.urls import path

from verification import views

urlpatterns = [
    path("request", views.verification_request),
    path("confirm", views.verification_confirm),
]
