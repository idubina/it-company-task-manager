from django.contrib.auth import get_user_model
from django.test import TestCase
from task_manager.models import *


User = get_user_model()

USERNAME_A = "worker_a"
USERNAME_B = "worker_b"
USERNAME_C = "worker_c"
USERNAME_D = "worker_d"
FIRST_NAME = "Wor"
LAST_NAME = "Ker"
TEAM_NAME = "Team"
PROJECT_NAME = "Project"
TASK_TYPE_NAME = "Task Type"
TASK_NAME = "Task"
TAG_NAME = "Tag"
POSITION_NAME = "Position"

class ModelStrClass(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.position = Position.objects.create(name=POSITION_NAME)
        cls.worker_full = User.objects.create(
            username=USERNAME_A,
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
            password="pass12345",
            position=cls.position
        )
        cls.worker_no_first_name = User.objects.create(
            username=USERNAME_B,
            last_name=LAST_NAME,
            password="pass12345",
            position=cls.position
        )
        cls.worker_no_last_name = User.objects.create(
            username=USERNAME_C,
            first_name=FIRST_NAME,
            password="pass12345",
            position=cls.position
        )
        cls.worker_no_position = User.objects.create(
            username=USERNAME_D,
            password="pass12345",
        )
        cls.team = Team.objects.create(name=TEAM_NAME)
        cls.project = Project.objects.create(name=PROJECT_NAME, team=cls.team)
        cls.task_type = TaskType.objects.create(name=TASK_TYPE_NAME)
        cls.task = Task.objects.create(name=TASK_NAME, project=cls.project)
        cls.tag =Tag.objects.create(name=TAG_NAME)

    def test_worker_full_data_str(self):
        self.assertEqual(
            str(self.worker_full),
            (
                f"{USERNAME_A}"
                f" ({FIRST_NAME} {LAST_NAME})"
                f" [{POSITION_NAME}]"
            )
        )

    def test_worker_no_first_name_str(self):
        self.assertEqual(
            str(self.worker_no_first_name),
            (
                f"{USERNAME_B}"
                f" [{POSITION_NAME}]"
            )
        )

    def test_worker_no_last_name_str(self):
        self.assertEqual(
            str(self.worker_no_last_name),
            (
                f"{USERNAME_C}"
                f" [{POSITION_NAME}]"
            )
        )

    def test_worker_no_position_str(self):
        self.assertEqual(
            str(self.worker_no_position),
            USERNAME_D
        )

    def test_position_str(self):
        self.assertEqual(str(self.position), POSITION_NAME)

    def test_team_str(self):
        self.assertEqual(str(self.team), TEAM_NAME)

    def test_task_type_str(self):
        self.assertEqual(str(self.task_type), TASK_TYPE_NAME)

    def test_tag_str(self):
        self.assertEqual(str(self.tag), TAG_NAME)

    def test_task_str(self):
        self.assertEqual(str(self.task), TASK_NAME)

    def test_project_str(self):
        self.assertEqual(str(self.project), PROJECT_NAME)
