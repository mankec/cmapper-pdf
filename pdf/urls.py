from django.urls import path

from . import views


app_name = "pdf"
urlpatterns = [
    path("upload/", views.upload, name="upload"),
    path("page/<int:pno>/", views.page, name="page"),
    path("page/<int:pno>/remap/<str:word>", views.remap, name="remap"),
]
