from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import (
    Q, When, Value, Case,
    IntegerField, Count, Prefetch
)
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.decorators.http import require_POST

from task_manager.forms import (
    WorkerUsernameSearchForm,
    TaskNameSearchForm,
    ProjectNameSearchForm,
    PositionNameSearchForm,
    TeamNameSearchForm,
    WorkerCreationForm,
    TaskTypeNameSearchForm,
    TagNameSearchForm,
    TaskForm,
    WorkerPositionUpdateForm,
    TeamCreateForm,
    ProjectForm,
    TeamUpdateForm,
    TagForm,
    TaskTypeForm,
    PositionForm,
    ChooseTeamForm,
    ChooseProjectForm
)
from task_manager.mixins import NextUrlRedirectMixin, StaffRequiredMixin
from task_manager.models import (
    Task,
    Project,
    Worker,
    Team,
    Position,
    Tag,
    TaskType
)


def _ensure_team_member(user, team: Team) -> None:
    if not user.is_authenticated:
        raise PermissionDenied
    if not team.members.filter(pk=user.pk).exists():
        raise PermissionDenied


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
        context["search_query"] = username
        return context

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("position")
        )
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
        )
        context["tasks_completed"] = (
            self.object.tasks
            .filter(is_completed=True)
        )
        context["teams"] = self.object.teams
        return context


class WorkerCreateView(LoginRequiredMixin, generic.CreateView):
    model = get_user_model()
    form_class = WorkerCreationForm
    success_url = reverse_lazy("task-manager:worker-list")


class WorkerPositionUpdateView(StaffRequiredMixin, generic.UpdateView):
    model = get_user_model()
    form_class = WorkerPositionUpdateForm

    def get_success_url(self):
        return reverse(
            "task-manager:worker-detail",
            kwargs={"pk": self.object.pk}
        )


class WorkerDeleteView(StaffRequiredMixin, generic.DeleteView):
    model = get_user_model()
    success_url = reverse_lazy("task-manager:worker-list")
    template_name = "task_manager/worker_confirm_delete.html"
    context_object_name = "worker"

    def _get_last_member_teams(self, worker):
        worker_team_ids = worker.teams.values_list("id", flat=True)
        return Team.objects.filter(id__in=worker_team_ids).annotate(
            member_count=Count("members", distinct=True)
        ).filter(member_count=1).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_member_teams = self._get_last_member_teams(self.object)

        context["worker_is_last_member_in_any_team"] = bool(last_member_teams)
        context["worker_last_member_teams"] = last_member_teams
        context["worker_last_member_teams_count"] = len(last_member_teams)
        context["worker_last_member_teams_names"] = (
            f"({', '.join(team.name for team in last_member_teams)})"
        )
        return context

    def form_valid(self, form):

        self.object = self.get_object()
        last_team_ids = list(
            self._get_last_member_teams(self.object)
            .values_list("id", flat=True)
        )

        response = super().form_valid(form)

        Team.objects.annotate(
            member_count=Count(
                "members", distinct=True)
        ).filter(
            id__in=last_team_ids,
            member_count=0
        ).delete()

        return response


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    paginate_by = 5

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):
        context = super(TaskListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = TaskNameSearchForm(initial={"name": name})
        context["search_query"] = name
        return context

    def get_queryset(self):
        queryset = (
            Task.objects
            .select_related("task_type", "project")
            .prefetch_related("assignees", "tags")
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
                            When(
                                name__icontains=query,
                                then=Value(1)
                            ),
                            When(
                                task_type__name__icontains=query,
                                then=Value(2)
                            ),
                            When(
                                tags__name__icontains=query,
                                then=Value(3)
                            ),
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
        .select_related("task_type", "project", "project__team")
        .prefetch_related(
            "tags",
            Prefetch(
                "assignees",
                queryset=Worker.objects.select_related("position")
            )
        )
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task_in_project_user_team"] = (
            self.object.project.team.members.filter(
                pk=self.request.user.pk
            ).exists()
        )
        return context


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            Project.objects.select_related("team"),
            pk=self.kwargs["project_pk"]
        )
        _ensure_team_member(request.user, self.project.team)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        return kwargs

    def form_valid(self, form):
        form.instance.project = self.project
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "task-manager:task-detail",
            kwargs={"pk": self.object.pk}
        )


class TaskUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm

    def get_queryset(self):
        return Task.objects.select_related("project__team").distinct()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        _ensure_team_member(request.user, self.object.project.team)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_object().project
        return kwargs

    def get_success_url(self):
        return reverse(
            "task-manager:task-detail",
            kwargs={"pk": self.object.pk}
        )


class TaskDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Task
    success_url = reverse_lazy("task-manager:task-list")

    def get_queryset(self):
        return Task.objects.select_related("project__team").distinct()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        _ensure_team_member(request.user, self.object.project.team)
        return super().dispatch(request, *args, **kwargs)


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
        context["search_query"] = name
        context["page_title"] = "All projects"
        context["is_user_projects_page"] = False
        context["user_team_ids"] = set(
            self.request.user.teams.values_list("id", flat=True)
        )
        return context

    def get_queryset(self):
        queryset = (
            Project.objects
            .select_related("team")
            .annotate(task_count=Count("tasks", distinct=True))
        )
        form = ProjectNameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                name__icontains=form.cleaned_data["name"]
            )
        return queryset


class UserProjectListView(LoginRequiredMixin, generic.ListView):
    model = Project
    paginate_by = 5
    template_name = "task_manager/project_list.html"

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):
        context = super(UserProjectListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = ProjectNameSearchForm(
            initial={"name": name}
        )
        context["search_query"] = name
        context["page_title"] = "My projects"
        context["is_user_projects_page"] = True
        context["user_team_ids"] = set(
            self.request.user.teams.values_list("id", flat=True)
        )
        return context

    def get_queryset(self):
        queryset = (
            Project.objects
            .select_related("team")
            .filter(team__members=self.request.user)
            .annotate(task_count=Count("tasks", distinct=True))
        )
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
        context = super().get_context_data(**kwargs)
        context["tasks_in_progress"] = (
            self.object.tasks.filter(is_completed=False)
        )
        context["tasks_completed"] = (
            self.object.tasks.filter(is_completed=True)
        )
        context["project_in_user_team"] = (
            self.object.team.members.filter(
                pk=self.request.user.pk
            ).exists()
        )
        return context


class ProjectCreateView(
    LoginRequiredMixin,
    NextUrlRedirectMixin,
    generic.CreateView
):
    model = Project
    form_class = ProjectForm

    def dispatch(self, request, *args, **kwargs):
        self.team = get_object_or_404(Team, pk=self.kwargs["team_pk"])
        _ensure_team_member(request.user, self.team)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.team = self.team
        return super().form_valid(form)

    def get_success_url(self):
        next_url = self.request.POST.get("next")

        if next_url:
            return next_url

        return reverse(
            "task-manager:project-detail",
            kwargs={"pk": self.object.pk}
        )


class ProjectUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Project
    form_class = ProjectForm

    def get_queryset(self):
        return Project.objects.select_related("team").distinct()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        _ensure_team_member(request.user, self.object.team)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "task-manager:project-detail",
            kwargs={"pk": self.object.pk}
        )


class ProjectDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Project
    success_url = reverse_lazy("task-manager:project-list")

    def get_queryset(self):
        return Project.objects.select_related("team").distinct()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        _ensure_team_member(request.user, self.object.team)
        return super().dispatch(request, *args, **kwargs)


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
        context["search_query"] = name
        return context

    def get_queryset(self):
        queryset = Position.objects.annotate(
            worker_count=Count("workers", distinct=True)
        )
        form = PositionNameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                name__icontains=form.cleaned_data["name"]
            )
        return queryset


class PositionCreateView(StaffRequiredMixin, generic.CreateView):
    model = Position
    form_class = PositionForm
    success_url = reverse_lazy("task-manager:position-list")


class PositionUpdateView(StaffRequiredMixin, generic.UpdateView):
    model = Position
    form_class = PositionForm

    def get_success_url(self):
        return reverse(
            "task-manager:position-detail",
            kwargs={"pk": self.object.pk}
        )


class PositionDetailView(LoginRequiredMixin, generic.DetailView):
    model = Position
    queryset = (
        Position.objects
        .prefetch_related("workers")
    )


class PositionDeleteView(StaffRequiredMixin, generic.DeleteView):
    model = Position
    success_url = reverse_lazy("task-manager:position-list")


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
        context["search_query"] = name
        context["page_title"] = f"All teams"
        context["is_user_team_page"] = False
        return context

    def get_queryset(self):
        queryset = Team.objects.annotate(
            member_count=Count("members", distinct=True)
        )
        form = TeamNameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                name__icontains=form.cleaned_data["name"]
            )
        return queryset


class UserTeamListView(LoginRequiredMixin, generic.ListView):
    model = Team
    paginate_by = 5
    template_name = "task_manager/team_list.html"

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):
        context = super(UserTeamListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = TeamNameSearchForm(
            initial={"name": name}
        )
        context["search_query"] = name
        context["page_title"] = f"My teams"
        context["is_user_team_page"] = True
        return context

    def get_queryset(self):
        queryset = (
            Team.objects
            .filter(members=self.request.user)
            .annotate(
                member_count=Count("members", distinct=True)
            )
            .prefetch_related("members")
        )
        form = TeamNameSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(
                name__icontains=form.cleaned_data["name"]
            )
        return queryset


class TeamDetailView(LoginRequiredMixin, generic.DetailView):
    model = Team
    queryset = Team.objects.prefetch_related(
        Prefetch(
            "members",
            queryset=Worker.objects.select_related("position")
        ),
        "projects",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_in_team"] = (
            self.object.members.filter(
                pk=self.request.user.pk
            ).exists()
        )
        return context


class TeamCreateView(
    LoginRequiredMixin,
    NextUrlRedirectMixin,
    generic.CreateView
):
    model = Team
    form_class = TeamCreateForm
    success_url = reverse_lazy("task-manager:team-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.members.count() == 0:
            self.object.members.add(self.request.user)
        return response

    def get_success_url(self):
        next_url = self.request.POST.get("next")

        if next_url:
            return next_url

        return reverse(
            "task-manager:team-detail",
            kwargs={"pk": self.object.pk}
        )


class TeamUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Team
    form_class = TeamUpdateForm

    def get_queryset(self):
        return Team.objects.prefetch_related("members").distinct()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        _ensure_team_member(request.user, self.object)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        team = self.get_object()
        old_member_ids = set(team.members.values_list("id", flat=True))

        response = super().form_valid(form)

        new_member_ids = set(self.object.members.values_list("id", flat=True))
        removed_member_ids = old_member_ids - new_member_ids

        if removed_member_ids:
            tasks = Task.objects.filter(
                project__team=self.object,
                assignees__id__in=removed_member_ids
            ).distinct()
            for task in tasks:
                task.assignees.remove(*removed_member_ids)

        return response

    def get_success_url(self):
        return reverse(
            "task-manager:team-detail",
            kwargs={"pk": self.object.pk}
        )


class TeamDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Team
    success_url = reverse_lazy("task-manager:team-list")

    def get_queryset(self):
        return Team.objects.distinct()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        _ensure_team_member(request.user, self.object)
        return super().dispatch(request, *args, **kwargs)


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
        context["search_query"] = name
        return context

    def get_queryset(self):
        queryset = Tag.objects
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
                            When(
                                name__icontains=query,
                                then=Value(1)
                            ),
                            When(
                                task_type__name__icontains=query,
                                then=Value(2)
                            ),
                            When(
                                tags__name__icontains=query,
                                then=Value(3)
                            ),
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
        context["page_title"] = f"Tasks with tag: #{self.tag.name}"
        context["empty_message"] = "There are no tasks with this tag."
        context["sub_title"] = context["page_title"].title()
        context["search_query"] = name
        return context


class TagCreateView(
    LoginRequiredMixin,
    NextUrlRedirectMixin,
    generic.CreateView
):
    model = Tag
    form_class = TagForm
    success_url = reverse_lazy("task-manager:tag-list")


class TagUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Tag
    form_class = TagForm
    success_url = reverse_lazy("task-manager:tag-list")


class TagDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Tag
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
        context["search_query"] = name
        return context

    def get_queryset(self):
        queryset = TaskType.objects
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
                            When(
                                name__icontains=query,
                                then=Value(1)
                            ),
                            When(
                                task_type__name__icontains=query,
                                then=Value(2)
                            ),
                            When(
                                tags__name__icontains=query,
                                then=Value(3)
                            ),
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
        context["page_title"] = f"Tasks with task type: {self.task_type.name}"
        context["empty_message"] = "There are no tasks with this task type."
        context["sub_title"] = context["page_title"].title()
        context["search_query"] = name
        return context


class TaskTypeCreateView(
    LoginRequiredMixin,
    NextUrlRedirectMixin,
    generic.CreateView
):
    model = TaskType
    form_class = TaskTypeForm
    success_url = reverse_lazy("task-manager:task-type-list")
    template_name = "task_manager/task_type_form.html"


class TaskTypeUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = TaskType
    form_class = TaskTypeForm
    success_url = reverse_lazy("task-manager:task-type-list")
    template_name = "task_manager/task_type_form.html"


class TaskTypeDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = TaskType
    success_url = reverse_lazy("task-manager:task-type-list")
    template_name = "task_manager/task_type_confirm_delete.html"


@require_POST
@login_required
def change_task_status(request, pk):
    task = get_object_or_404(
        Task.objects.select_related("project__team"),
        pk=pk,
    )

    if not task.project.team.members.filter(pk=request.user.pk).exists():
        raise PermissionDenied

    task.is_completed = not task.is_completed
    task.save(update_fields=["is_completed"])

    return redirect("task-manager:task-detail", pk=task.pk)


class TaskCreateSelectTeamView(LoginRequiredMixin, generic.FormView):
    form_class = ChooseTeamForm
    template_name = "task_manager/task_choose_team.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["has_teams"] = (
            Team.objects.filter(
                members=self.request.user
            ).exists()
        )
        return context

    def form_valid(self, form):
        team = form.cleaned_data["team"]
        url = reverse("task-manager:task-create-select-project")
        return redirect(f"{url}?team={team.pk}")


class TaskCreateSelectProjectView(LoginRequiredMixin, generic.FormView):
    form_class = ChooseProjectForm
    template_name = "task_manager/task_choose_project.html"

    def dispatch(self, request, *args, **kwargs):
        team_id = request.GET.get("team")

        if not team_id:
            return redirect("task-manager:task-create-select-team")

        self.team = get_object_or_404(Team, pk=team_id)
        _ensure_team_member(request.user, self.team)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["team"] = self.team
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(). get_context_data()
        context["team"] = self.team
        context["has_projects"] = (
            Project.objects.filter(
                team=self.team
            ).exists()
        )
        return context

    def form_valid(self, form):
        project = form.cleaned_data["project"]
        return redirect("task-manager:task-create", project_pk=project.id)


class ProjectCreateSelectTeamView(LoginRequiredMixin, generic.FormView):
    form_class = ChooseTeamForm
    template_name = "task_manager/project_choose_team.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_teams"] = (
            Team.objects.filter(
                members=self.request.user
            ).exists()
        )
        return context

    def form_valid(self, form):
        team = form.cleaned_data["team"]
        return redirect("task-manager:project-create", team_pk=team.id)
