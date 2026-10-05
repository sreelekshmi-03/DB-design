from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, Employer, Candidate, Job, Application


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Extends Django's built-in UserAdmin instead of registering plainly,
    so password hashing and the "change password" form still work correctly.
    """
    model = User
    ordering = ("-created_at",)
    list_display = ("email", "username", "role", "is_verified", "is_active", "created_at")
    list_filter = ("role", "is_verified", "is_active", "is_staff")
    search_fields = ("email", "username", "phone")

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone")}),
        ("Role & status", {"fields": ("role", "is_verified", "is_active", "is_staff", "is_superuser")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "role", "password1", "password2"),
        }),
    )


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ("company_name", "user",  "created_at")
    search_fields = ("company_name", "user__email")


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "created_at")
    search_fields = ("full_name", "user__email")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "employer__company_name")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("candidate", "job", "status", "ats_score", "created_at")
    list_filter = ("status",)