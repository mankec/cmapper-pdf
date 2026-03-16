# from django.contrib import admin
from django.urls import include, path

from pdf import views as pdf_views


urlpatterns = [
    path("", pdf_views.index, name="index"), # Root
    path("pdf/", include("pdf.urls")),
    # path("admin/", admin.site.urls),
]
