from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve

from cars import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("favicon.ico", views.favicon_view, name="favicon"),
    path("", views.home, name="home"),
    path("profile/", views.profile_view, name="profile"),
    path("garage/add/", views.add_car_view, name="add_car"),
    path("garage/edit/<int:car_id>/", views.edit_car_view, name="edit_car"),
    path("cars/", views.car_list, name="car_list"),
    path("favorites/", views.favorites_view, name="favorites"),
    path("favorites/toggle/<int:car_id>/", views.toggle_favorite_view, name="toggle_favorite"),
    path("compare/", views.compare, name="compare"),
    path("login/", views.login_view, name="login"),
    path("activate/<uidb64>/<token>/", views.activate_account_view, name="activate_account"),
    path("login/email/", views.email_login_request_view, name="email_login_request"),
    path("login/email/<uidb64>/<token>/", views.magic_login_verify_view, name="magic_login_verify"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
