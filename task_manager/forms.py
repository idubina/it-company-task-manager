from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from task_manager.models import Team, Task, Tag, Project, TaskType, Position


class WorkerUsernameSearchForm(forms.Form):
    username = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "username..."})
    )


class WorkerCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = UserCreationForm.Meta.fields + (
            "first_name",
            "last_name",
            "email",
            "position",
        )


class WorkerPositionUpdateForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["position"]


class TaskNameSearchForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "name, type, or tag...",})
    )


class ProjectNameSearchForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "project name..."})
    )


class PositionNameSearchForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "position name..."})
    )


class TagNameSearchForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "tag..."})
    )


class TaskTypeNameSearchForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "task type..."})
    )


class TaskForm(forms.ModelForm):
    assignees = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    class Meta:
        model = Task
        fields = (
            "name",
            "task_type",
            "description",
            "priority",
            "assignees",
            "deadline",
            "tags",
            "is_completed",
        )

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        if self.project is None and self.instance and self.instance.pk:
            self.project = self.instance.project

        if self.project:
            self.fields["assignees"].queryset = self.project.team.members

    def clean_assignees(self):
        assignees = self.cleaned_data.get("assignees")
        if not self.project:
            return assignees

        team_member_ids = set(self.project.team.members.values_list("id", flat=True))
        invalid = [u.username for u in assignees if u.id not in team_member_ids]
        if invalid:
            raise forms.ValidationError(
                f"Only team members can be assignees. Invalid: {', '.join(invalid)}"
            )
        return assignees


class TeamNameSearchForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "team name..."})
    )


class TeamCreateForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Team
        fields = ("name", "members")

    def clean_name(self):
        name = self.cleaned_data["name"]

        if len(name) > 30:
            raise ValidationError(
                "Team name is too long (max 30 characters)"
            )

        return name


class TeamUpdateForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all().order_by("username"),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Team
        fields = ("name", "members")

    def clean_members(self):
        members = self.cleaned_data.get("members")
        if not members:
            raise forms.ValidationError("Team must have at least one member.")
        return members

    def clean_name(self):
        name = self.cleaned_data["name"]

        if len(name) > 30:
            raise ValidationError(
                "Team name is too long (max 30 characters)"
            )

        return name


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description")

    def clean_name(self):
        name = self.cleaned_data["name"]

        if len(name) > 30:
            raise ValidationError(
                "Project name is too long (max 30 characters)"
            )

        return name


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = "__all__"

    def clean_name(self):
        name = self.cleaned_data["name"]

        if name[0] == "#":
            raise ValidationError(
                "Tag can not start with '#'"
            )


        if len(name) > 20:
            raise ValidationError(
                "Tag is too long (max 20 characters)"
            )
        return "-".join([word.lower() for word in name.split()])


class TaskTypeForm(forms.ModelForm):
    class Meta:
        model = TaskType
        fields = "__all__"

    def clean_name(self):
        name = self.cleaned_data["name"]

        if len(name) > 30:
            raise ValidationError(
                "Task type name is too long (max 30 characters)"
            )

        return " ".join([word.capitalize() for word in name.split()])


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = "__all__"

    def clean_name(self):
        name = self.cleaned_data["name"]

        if len(name) > 30:
            raise ValidationError(
                "Position name is too long (max 30 characters)"
            )

        return name
