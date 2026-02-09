from django.urls import path
from task_manager.views import (
    index,
    WorkerListView,
    TaskListView,
    ProjectListView,
    PositionListView,
    TeamListView,
    TaskDetailView,
    WorkerDetailView,
    PositionDetailView,
    ProjectDetailView,
    TeamDetailView,
    PositionCreateView,
    TeamCreateView,
    ProjectCreateView,
    WorkerCreateView,
)

urlpatterns = [
    path("", index, name="index"),
    path("workers/", WorkerListView.as_view(), name="worker-list"),
    path("workers/<int:pk>/", WorkerDetailView.as_view(), name="worker-detail"),
    path("workers/create/", WorkerCreateView.as_view(), name="worker-create"),
    path("tasks/", TaskListView.as_view(), name="task-list"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/create", ProjectCreateView.as_view(), name="project-create"),
    path("positions/<int:pk>/", PositionDetailView.as_view(), name="position-detail"),
    path("positions/", PositionListView.as_view(), name="position-list"),
    path("positions/create/", PositionCreateView.as_view(), name="position-create"),
    path("teams/", TeamListView.as_view(), name="team-list"),
    path("teams/create/", TeamCreateView.as_view(), name="team-create"),
    path("teams/<int:pk>/", TeamDetailView.as_view(), name="team-detail"),
]


app_name = "task-manager"