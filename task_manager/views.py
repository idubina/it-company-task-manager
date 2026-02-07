from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views import generic

from task_manager.forms import WorkerUsernameSearchForm, TaskNameSearchForm
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
    paginate_by = 5

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):
        context = super(WorkerListView, self).get_context_data(**kwargs)
        username = self.request.GET.get("username", "")
        context["search_form"] = WorkerUsernameSearchForm(
            initial={"username": username}
        )
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        form = WorkerUsernameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                username__icontains=form.cleaned_data["username"]
            )
        return queryset

class TaskListView(generic.ListView):
    model = Task
    paginate_by = 5

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):
        context = super(TaskListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = TaskNameSearchForm(initial={"name": name})
        return context

    def get_queryset(self):
        queryset = (
            Task.objects
            .select_related("task_type", "project")
            .prefetch_related("tags")
        )
        form = TaskNameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(name__icontains=form.cleaned_data["name"])
        return queryset
