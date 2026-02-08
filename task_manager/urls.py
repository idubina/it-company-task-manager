from django.urls import path
from task_manager.views import (
    index,
    WorkerListView,
    TaskListView,
    ProjectListView,
    PositionListView,
    TeamListView,
    TaskDetailView
)

urlpatterns = [
    path("", index, name="index"),
    path("workers/", WorkerListView.as_view(), name="worker-list"),
    path("tasks/", TaskListView.as_view(), name="task-list"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("positions/", PositionListView.as_view(), name="position-list"),
    path("teams/", TeamListView.as_view(), name="team-list"),
]


app_name = "task-manager"