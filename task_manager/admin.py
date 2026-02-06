from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Worker,
    TaskType,
    Task,
    Position,
    Project,
    Team,
    Tag
)


@admin.register(Worker)
class WorkerAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("position",)
    fieldsets = UserAdmin.fieldsets + (
        (("Additional info", {"fields": ("position",)}),)
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            (
                "Additional info",
                {
                    "fields": (
                        "first_name",
                        "last_name",
                        "position",
                    )
                },
            ),
        )
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "get_tags",
        "priority",
        "is_completed",
        "deadline",
        "task_type",
        "project",
    ]

    @admin.display(description="Tags")
    def get_tags(self, obj):
        return ", ".join(f"#{tag.name}" for tag in obj.tags.all())


admin.site.register(TaskType)
admin.site.register(Position)
admin.site.register(Project)
admin.site.register(Team)
admin.site.register(Tag)
