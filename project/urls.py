from django.contrib import admin
from django.urls import path

from core import views as core_views


urlpatterns = [
    path("", core_views.index, name="index"), # Root
    path("admin/", admin.site.urls),
]
