from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """Default manager - hides soft-deleted rows from every normal query."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    """
    Adds soft-delete instead of a real DB delete. Day 11 asks for "soft
    delete logic" on profiles: a candidate/employer who deactivates their
    account shouldn't vanish from Application/Job history - their data
    just stops showing up in normal queries and normal profile lookups.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()        # default: excludes deleted rows
    all_objects = models.Manager()       # explicit: includes everything (admin use)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


# ---------------------------------------------------------------- User
class User(AbstractUser, TimeStampedModel):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EMPLOYER = "employer", "Employer"
        CANDIDATE = "candidate", "Candidate"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CANDIDATE)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_employer_role(self):
        return self.role == self.Role.EMPLOYER

    @property
    def is_candidate_role(self):
        return self.role == self.Role.CANDIDATE


# ------------------------------------------------------------ Employer
class Employer(TimeStampedModel, SoftDeleteModel):
    class CompanySize(models.TextChoices):
        MICRO = "1-10", "1-10 employees"
        SMALL = "11-50", "11-50 employees"
        MEDIUM = "51-200", "51-200 employees"
        LARGE = "201-1000", "201-1000 employees"
        ENTERPRISE = "1000+", "1000+ employees"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employer_profile"
    )
    company_name = models.CharField(max_length=255, blank=True)
    domain = models.CharField(
        max_length=255, blank=True,
        help_text="Company website domain, e.g. zecpath.com (used to sanity-check company emails).",
    )
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=20, choices=CompanySize.choices, blank=True)
    is_company_verified = models.BooleanField(
        default=False, help_text="Set by an admin once the company/domain is manually verified."
    )

    class Meta:
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name or self.user.email


# ----------------------------------------------------------- Candidate
class Candidate(TimeStampedModel, SoftDeleteModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="candidate_profile"
    )
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    resume = models.FileField(
        upload_to="resumes/", blank=True,
        validators=[FileExtensionValidator(["pdf", "doc", "docx"])],
    )
    skills = models.JSONField(default=list, blank=True, help_text='e.g. ["Python", "Django"]')
    education = models.JSONField(
        default=list, blank=True,
        help_text='e.g. [{"degree": "B.Tech CSE", "institution": "KTU", "year": 2025}]',
    )
    experience_years = models.PositiveSmallIntegerField(default=0)
    expected_salary = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)],
        help_text="Annual expected salary, in the platform's base currency.",
    )

    def __str__(self):
        return self.full_name or self.user.email


# ----------------------------------------------------------------- Job
class Job(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# --------------------------------------------------------- Application
class Application(TimeStampedModel):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        SHORTLISTED = "shortlisted", "Shortlisted"
        REJECTED = "rejected", "Rejected"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.APPLIED)
    ats_score = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["job", "candidate"], name="unique_application_per_job")
        ]

    def __str__(self):
        return f"{self.candidate} -> {self.job}"