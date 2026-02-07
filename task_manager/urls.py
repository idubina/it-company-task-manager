from django.urls import path
from task_manager.views import (
    index,
    WorkerListView,
    TaskListView,
    ProjectListView
)

urlpatterns = [
    path("", index, name="index"),
    path("workers/", WorkerListView.as_view(), name="worker-list"),
    path("tasks/", TaskListView.as_view(), name="task-list"),
    path("projects/", ProjectListView.as_view(), name="project-list"),
]


app_name = "task-manager"