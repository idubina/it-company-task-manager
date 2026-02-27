from django.contrib.auth import get_user_model
from django.test import TestCase

from task_manager.forms import TaskForm, TeamUpdateForm, TagForm, TaskTypeForm
from task_manager.models import Team, Project, TaskType, Tag, Task

User = get_user_model()


class TaskFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.member = User.objects.create(
            username="member",
            password="pass12345"
        )
        cls.outsider = User.objects.create(
            username="outsider",
            password="pass12345"
        )

        cls.team = Team.objects.create(name="Team")
        cls.team.members.add(cls.member)

        cls.project = Project.objects.create(name="Project", team=cls.team)
        cls.task_type = TaskType.objects.create(name="Task Type")
        cls.tag = Tag.objects.create(name="Tag")

    def test_clean_assignees_rejects_worker_outside_team(self):
        form = TaskForm(
            data={
                "name": "Task",
                "description": "",
                "task_type": self.task_type.id,
                "priority": Task.PriorityChoices.MEDIUM,
                "assignees": [self.outsider.id],
                "tags": [self.tag.id],
                "deadline": ""
            },
            project=self.project
        )

        form.fields["assignees"].queryset = User.objects.all()

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Only team members can be assignees.",
            form.errors["assignees"][0]
        )

    def test_clean_assignees_allows_team_member(self):
        form = TaskForm(
            data={
                "name": "Task",
                "description": "",
                "task_type": self.task_type.id,
                "priority": Task.PriorityChoices.MEDIUM,
                "assignees": [self.member.id],
                "tags": [self.tag.id],
                "deadline": ""
            },
            project=self.project
        )

        self.assertTrue(form.is_valid())


class TeamUpdateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.worker_1 = User.objects.create(
            username="worker_1",
            password="pass12345"
        )
        cls.worker_2 = User.objects.create(
            username="worker_2",
            password="pass12345"
        )

        cls.team = Team.objects.create(name="Team")
        cls.team.members.add(cls.worker_1)

    def test_team_update_form_requires_at_least_one_member(self):
        form = TeamUpdateForm(
            instance=self.team,
            data={
                "name": "Team",
                "members": []
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Team must have at least one member.",
            form.errors["members"][0]
        )

    def test_team_update_form_valid_with_members(self):
        form = TeamUpdateForm(
            instance=self.team,
            data={
                "name": "Team",
                "members": [self.worker_1.id, self.worker_2.id]
            }
        )
        self.assertTrue(form.is_valid())


class TagAndTaskFormTests(TestCase):

    def test_tag_form_rejects_hash_prefix(self):
        form = TagForm(data={"name": "#tag"})
        self.assertFalse(form.is_valid())
        self.assertIn("Tag can not start with '#'", form.errors["name"][0])

    def test_tag_form_normalizes_name(self):
        form = TagForm(data={"name": "TaG or teg"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "tag-or-teg")

    def test_task_type_form_normalizes_name(self):
        form = TaskTypeForm(data={"name": "taSk typE"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "Task Type")
