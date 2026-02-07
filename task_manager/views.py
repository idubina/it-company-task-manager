from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views import generic

from task_manager.models import (
    Task,
    Project,
    Worker,
    Team,
    Position
)
def index(request):

    num_teams = Team.objects.count()
    num_workers = Worker.objects.count()
    num_positions = Position.objects.count()
    num_projects = Project.objects.count()
    num_tasks = Task.objects.count()

    context = {
        "num_teams": num_teams,
        "num_workers": num_workers,
        "num_positions": num_positions,
        "num_projects": num_projects,
        "num_tasks": num_tasks,
    }

    return render(request, "task_manager/index.html", context=context)


class WorkerListView(generic.ListView):
    model = get_user_model()
