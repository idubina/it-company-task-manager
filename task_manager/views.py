from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, When, Value, Case, IntegerField
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import generic

from task_manager.forms import WorkerUsernameSearchForm, TaskNameSearchForm, ProjectNameSearchForm, \
    PositionNameSearchForm, TeamNameSearchForm, TeamForm, WorkerCreationForm, TaskTypeNameSearchForm, \
    TagNameSearchForm, TaskForm, WorkerPositionUpdateForm
from task_manager.mixins import NextUrlRedirectMixin
from task_manager.models import (
    Task,
    Project,
    Worker,
    Team,
    Position, Tag, TaskType
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


class WorkerCreateView(LoginRequiredMixin, NextUrlRedirectMixin, generic.CreateView):
    model = get_user_model()
    form_class = WorkerCreationForm
    success_url = reverse_lazy("task-manager:worker-list")


class WorkerPositionUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = get_user_model()
    form_class = WorkerPositionUpdateForm

    def get_success_url(self):
        return reverse("task-manager:worker-detail", kwargs={"pk": self.object.pk})


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


class TaskCreateView(LoginRequiredMixin, NextUrlRedirectMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy("task-manager:task-list")


class TaskUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm

    def get_success_url(self):
        return reverse("task-manager:task-detail", kwargs={"pk": self.object.pk})

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


class ProjectCreateView(LoginRequiredMixin, NextUrlRedirectMixin, generic.CreateView):
    model = Project
    fields = "__all__"
    success_url = reverse_lazy("task-manager:project-list")


class ProjectUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Project
    fields = "__all__"

    def get_success_url(self):
        return reverse("task-manager:project-detail", kwargs={"pk": self.object.pk})


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


class PositionCreateView(LoginRequiredMixin, NextUrlRedirectMixin, generic.CreateView):
    model = Position
    fields = "__all__"
    success_url = reverse_lazy("task-manager:position-list")


class PositionUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Position
    fields = "__all__"

    def get_success_url(self):
        return reverse("task-manager:position-detail", kwargs={"pk": self.object.pk})

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


class TeamCreateView(LoginRequiredMixin, NextUrlRedirectMixin, generic.CreateView):
    model = Team
    form_class = TeamForm
    success_url = reverse_lazy("task-manager:team-list")


class TeamUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Team
    form_class = TeamForm

    def get_success_url(self):
        return reverse("task-manager:team-detail", kwargs={"pk": self.object.pk})

class TagListView(LoginRequiredMixin, generic.ListView):
    model = Tag
    paginate_by = 5

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):
        context = super(TagListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = TagNameSearchForm(
            initial={"name": name}
        )
        return context

    def get_queryset(self):
        queryset = Tag.objects.order_by("name")
        form = TagNameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                name__icontains=form.cleaned_data["name"]
            )
        return queryset


class TagDetailView(LoginRequiredMixin, generic.ListView):
    model = Task
    template_name = "task_manager/task_list.html"
    context_object_name = "task_list"
    paginate_by = 5

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, pk=self.kwargs["pk"])

        queryset = (
            Task.objects
            .filter(tags=self.tag)
            .select_related("task_type", "project")
            .prefetch_related("assignees", "tags")
            .order_by("name")
            .distinct()
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = TaskNameSearchForm(initial={"name": name})
        context["page_title"] = f"Task with tag: {self.tag.name}"
        context["empty_message"] = "There are no tasks with this tag."
        return context


class TagCreateView(LoginRequiredMixin, NextUrlRedirectMixin, generic.CreateView):
    model = Tag
    fields = "__all__"
    success_url = reverse_lazy("task-manager:tag-list")


class TagUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Tag
    fields = "__all__"
    success_url = reverse_lazy("task-manager:tag-list")


class TaskTypeListView(LoginRequiredMixin, generic.ListView):
    model = TaskType
    context_object_name = "task_type_list"
    template_name = "task_manager/task_type_list.html"
    paginate_by = 5


    def get_context_data(
        self, *, object_list=None, **kwargs
    ):
        context = super(TaskTypeListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = TaskTypeNameSearchForm(
            initial={"name": name}
        )
        return context


    def get_queryset(self):
        queryset = TaskType.objects.order_by("name")
        form = TaskTypeNameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                name__icontains=form.cleaned_data["name"]
            )
        return queryset


class TaskTypeDetailView(LoginRequiredMixin, generic.ListView):
    model = TaskType
    context_object_name = "task_list"
    template_name = "task_manager/task_list.html"
    paginate_by = 5

    def get_queryset(self):
        self.task_type = get_object_or_404(TaskType, pk=self.kwargs["pk"])

        queryset = (
            Task.objects
            .filter(task_type=self.task_type)
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = TaskNameSearchForm(initial={"name": name})
        context["page_title"] = f"Task with task type: {self.task_type.name}"
        context["empty_message"] = "There are no tasks with this task type."
        return context


class TaskTypeCreateView(LoginRequiredMixin, NextUrlRedirectMixin, generic.CreateView):
    model = TaskType
    fields = "__all__"
    success_url = reverse_lazy("task-manager:task-type-list")
    template_name = "task_manager/task_type_form.html"


class TaskTypeUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = TaskType
    fields = "__all__"
    success_url = reverse_lazy("task-manager:task-type-list")
    template_name = "task_manager/task_type_form.html"
