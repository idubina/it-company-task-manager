from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from task_manager.models import Team, Project, Task

User = get_user_model()


class SmokeViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = User.objects.create(username="member", password="pass12345")
        cls.team = Team.objects.create(name="Team")
        cls.team.members.add(cls.member)

        cls.project = Project.objects.create(name="Project", team=cls.team)
        cls.task = Task.objects.create(
            name="Task",
            project=cls.project
        )

    def test_lists_and_index_pages_return_200_for_logged_in_user(self):
        page_names = [
            "index",
            "worker-list",
            "position-list",
            "team-list",
            "project-list",
            "task-list",
            "task-type-list",
            "tag-list"
        ]

        self.client.force_login(self.member)

        for page_name in page_names:
            with self.subTest(page=page_name):
                resp = self.client.get(reverse(f"task-manager:{page_name}"))
                self.assertEqual(
                    resp.status_code,
                    200,
                    msg=f"{page_name} returned {resp.status_code}"
                )


    def test_details_return_200_for_team_member(self):
        detail_pages_data = {
            "team_detail": {
                "page_name": "task-manager:team-detail",
                "pk": self.team.id,
                "user_context": "user_in_team",
            },
            "project_detail": {
                "page_name": "task-manager:project-detail",
                "pk": self.project.id,
                "user_context": "project_in_user_team",
            },
            "task_detail": {
                "page_name": "task-manager:task-detail",
                "pk": self.task.id,
                "user_context": "task_in_project_user_team",
            },
        }

        self.client.force_login(self.member)
        for key, detail_page in detail_pages_data.items():
            with self.subTest(page=key):
                resp = self.client.get(
                    reverse(
                        detail_page["page_name"],
                        kwargs={"pk": detail_page["pk"]}
                    )
                )
                self.assertEqual(
                    resp.status_code,
                    200,
                    msg=f"{key} returned {resp.status_code}"
                )
                self.assertIn(
                    detail_page["user_context"],
                    resp.context,
                    msg=(
                        f'Missing "{detail_page["user_context"]}" in context for '
                        f'{detail_page["page_name"]} (pk={detail_page["pk"]}).'
                    ),
                )
                self.assertTrue(
                    resp.context[detail_page["user_context"]],
                    msg=(
                        f'Context flag "{detail_page["user_context"]}" is False for '
                        f'{detail_page["page_name"]} (pk={detail_page["pk"]}).'
                    ),
                )
