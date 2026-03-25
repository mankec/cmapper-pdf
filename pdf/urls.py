from django.urls import path

from . import views


app_name = "pdf"
urlpatterns = [
    path("upload/", views.upload, name="upload"),
    path("page/<int:pno>/", views.page, name="page"),
    path("page/<int:pno>/<str:word>/", views.word, name="word"),
    path("page/<int:pno>/<str:word>/remap/", views.remap, name="remap"),
]
