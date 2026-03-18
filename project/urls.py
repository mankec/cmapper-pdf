# from django.contrib import admin
from django.urls import include, path

from core import views as core_views


urlpatterns = [
    path("", core_views.index, name="index"), # Root
    path("pdf/", include("pdf.urls")),
    # path("admin/", admin.site.urls),
]
