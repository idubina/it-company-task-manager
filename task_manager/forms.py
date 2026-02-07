from django import forms


class WorkerUsernameSearchForm(forms.Form):
    username = forms.CharField(max_length=150, required=False, label="")
