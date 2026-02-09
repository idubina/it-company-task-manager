from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, When, Value, Case, IntegerField
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from task_manager.forms import WorkerUsernameSearchForm, TaskNameSearchForm, ProjectNameSearchForm, \
    PositionNameSearchForm, TeamNameSearchForm
from task_manager.models import (
    Task,
    Project,
    Worker,
    Team,
    Position
)


@login_required
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


class WorkerListView(LoginRequiredMixin, generic.ListView):
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
        queryset = super().get_queryset().order_by("id")
        form = WorkerUsernameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                username__icontains=form.cleaned_data["username"]
            )
        return queryset


class WorkerDetailView(LoginRequiredMixin, generic.DetailView):
    model = Worker

    def get_queryset(self):
        return (
        Worker.objects
        .select_related("position")
        .prefetch_related("teams")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tasks_in_progress"] = (
            self.object.tasks
            .filter(is_completed=False)
            .order_by("name")
        )
        context["tasks_completed"] = (
            self.object.tasks
            .filter(is_completed=True)
            .order_by("name")
        )
        context["teams"] = self.object.teams.order_by("name")
        return context


class TaskListView(LoginRequiredMixin, generic.ListView):
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
            .prefetch_related("assignees", "tags")
            .order_by("name")
        )
        form = TaskNameSearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data.get("name")
            if query:
                queryset = (
                    queryset
                    .filter(
                        Q(name__icontains=query) |
                        Q(task_type__name__icontains=query) |
                        Q(tags__name__icontains=query)
                    )
                    .annotate(
                        search_rank=Case(
                            When(name__icontains=query, then=Value(1)),
                            When(task_type__name__icontains=query, then=Value(2)),
                            When(tags__name__icontains=query, then=Value(3)),
                            default=Value(4),
                            output_field=IntegerField(),
                        )
                    )
                    .order_by("search_rank", "name")
                    .distinct()
                )

        return queryset


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = Task
    queryset = (
        Task.objects
        .select_related("task_type", "project")
        .prefetch_related("tags", "assignees")
    )


class ProjectListView(LoginRequiredMixin, generic.ListView):
    model = Project
    paginate_by = 5

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = ProjectNameSearchForm(
            initial={"name": name}
        )
        return context

    def get_queryset(self):
        queryset = super().get_queryset().order_by("name")
        form = ProjectNameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                name__icontains=form.cleaned_data["name"]
            )
        return queryset


class ProjectDetailView(LoginRequiredMixin, generic.DetailView):
    model = Project
    queryset = Project.objects.select_related("team")

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        context["tasks_in_progress"] = (
            self.object.tasks
            .filter(is_completed=False)
            .order_by("name")
        )
        context["tasks_completed"] = (
            self.object.tasks
            .filter(is_completed=True)
            .order_by("name")
        )
        return context

class PositionListView(LoginRequiredMixin, generic.ListView):
    model = Position
    paginate_by = 5

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):
        context = super(PositionListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = PositionNameSearchForm(
            initial={"name": name}
        )
        return context

    def get_queryset(self):
        queryset = super().get_queryset().order_by("name")
        form = PositionNameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                name__icontains=form.cleaned_data["name"]
            )
        return queryset


class PositionCreateView(LoginRequiredMixin, generic.CreateView):
    model = Position
    fields = "__all__"
    success_url = reverse_lazy("task-manager:position-list")


class PositionDetailView(LoginRequiredMixin, generic.DetailView):
    model = Position
    queryset = (
        Position.objects
        .prefetch_related("workers")
        .order_by("workers__username")
    )


class TeamListView(LoginRequiredMixin, generic.ListView):
    model = Team
    paginate_by = 5

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):
        context = super(TeamListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = TeamNameSearchForm(
            initial={"name": name}
        )
        return context

    def get_queryset(self):
        queryset = Team.objects.prefetch_related("members").order_by("name")
        form = TeamNameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                name__icontains=form.cleaned_data["name"]
            )
        return queryset


class TeamDetailView(LoginRequiredMixin, generic.DetailView):
    model = Team
    queryset = Team.objects.prefetch_related("members", "project_set")
