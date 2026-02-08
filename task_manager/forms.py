from django import forms


class WorkerUsernameSearchForm(forms.Form):
    username = forms.CharField(max_length=150, required=False, label="")


class TaskNameSearchForm(forms.Form):
    name = forms.CharField(max_length=255, required=False, label="")


class ProjectNameSearchForm(forms.Form):
    name = forms.CharField(max_length=255, required=False, label="")


class PositionNameSearchForm(forms.Form):
    name = forms.CharField(max_length=255, required=False, label="")


class TeamNameSearchForm(forms.Form):
    name = forms.CharField(max_length=255, required=False, label="")