from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from task_manager.models import Team, Project, Task, TaskType


User = get_user_model()


@override_settings(
    DEBUG=False,
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
)
class BaseAccessTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(
            username="staff",
            password="pass12345",
            is_staff=True
        )
        cls.member_a = User.objects.create_user(
            username="member_a",
            password="pass12345"
        )
        cls.member_b = User.objects.create_user(
            username="member_b",
            password="pass12345"
        )
        cls.outsider = User.objects.create_user(
            username="outsider",
            password="pass12345"
        )

        cls.team_a = Team.objects.create(name="Team A")
        cls.team_b = Team.objects.create(name="Team B")
        cls.team_a.members.add(cls.member_a)
        cls.team_b.members.add(cls.member_b)

        cls.project_a = Project.objects.create(
            name="Project A",
            description="desc",
            team=cls.team_a
        )
        cls.task_type = TaskType.objects.create(name="Bug")
        cls.task_a = Task.objects.create(
            name="Task A",
            project=cls.project_a,
            task_type=cls.task_type,
            is_completed=False
        )

    def login(self, user):
        self.client.force_login(user)


class Forbidden403Tests(BaseAccessTestCase):
    def test_non_member_gets_403_on_project_update(self):
        self.login(self.member_b)
        url = reverse(
            "task-manager:project-update",
            kwargs={"pk": self.project_a.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")

    def test_non_member_gets_403_on_project_delete(self):
        self.login(self.outsider)
        url = reverse(
            "task-manager:project-delete",
            kwargs={"pk": self.project_a.pk}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")

    def test_non_member_gets_403_on_change_task_status(self):
        self.login(self.member_b)
        url = reverse(
            "task-manager:task-change-status",
            kwargs={"pk": self.task_a.pk}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")

    def test_non_staff_gets_403_on_worker_delete(self):
        self.login(self.member_a)
        url = reverse(
            "task-manager:worker-delete",
            kwargs={"pk": self.member_b.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")

    def test_team_member_can_change_task_status(self):
        self.login(self.member_a)
        url = reverse(
            "task-manager:task-change-status",
            kwargs={"pk": self.task_a.pk}
        )

        response = self.client.post(url)

        self.assertIn(response.status_code, (302, 303))
        self.task_a.refresh_from_db()
        self.assertTrue(self.task_a.is_completed)


class NotFound404Tests(BaseAccessTestCase):
    def test_missing_project_update_returns_404(self):
        self.login(self.member_a)
        url = reverse("task-manager:project-update", kwargs={"pk": 999999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_missing_task_change_status_returns_404(self):
        self.login(self.member_a)
        url = reverse("task-manager:task-change-status", kwargs={"pk": 999999})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_missing_worker_delete_returns_404_for_staff(self):
        self.login(self.staff)
        url = reverse("task-manager:worker-delete", kwargs={"pk": 999999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_unknown_url_returns_404(self):
        self.login(self.member_a)
        response = self.client.get("/definitely-missing-page/")

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
