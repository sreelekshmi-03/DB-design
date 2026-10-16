
import django_filters
from django.db.models import Q

from app.models import Job, Application


class JobFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Job.Status.choices)
    job_type = django_filters.ChoiceFilter(choices=Job.JobType.choices)

    location = django_filters.CharFilter(
        field_name="location",
        lookup_expr="icontains",
    )
    skill = django_filters.CharFilter(
        field_name="skills",
        lookup_expr="icontains",
    )

    experience_min = django_filters.NumberFilter(
        field_name="experience_years",
        lookup_expr="gte",
    )
    experience_max = django_filters.NumberFilter(
        field_name="experience_years",
        lookup_expr="lte",
    )

    salary_min = django_filters.NumberFilter(method="filter_salary_min")
    salary_max = django_filters.NumberFilter(method="filter_salary_max")

    created_after = django_filters.DateFilter(
        field_name="created_at__date",
        lookup_expr="gte",
    )
    created_before = django_filters.DateFilter(
        field_name="created_at__date",
        lookup_expr="lte",
    )

    class Meta:
        model = Job
        fields = [
            "status",
            "job_type",
            "location",
            "skill",
            "experience_min",
            "experience_max",
            "salary_min",
            "salary_max",
            "created_after",
            "created_before",
        ]

    def filter_salary_min(self, queryset, name, value):
        # Include jobs whose maximum salary meets the requested minimum,
        # or whose maximum salary is unspecified.
        return queryset.filter(
            Q(salary_max__gte=value) | Q(salary_max__isnull=True)
        )

    def filter_salary_max(self, queryset, name, value):
        # Include jobs whose minimum salary is within the requested maximum,
        # or whose minimum salary is unspecified.
        return queryset.filter(
            Q(salary_min__lte=value) | Q(salary_min__isnull=True)
        )


class ApplicationFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Application.Status.choices)
    created_after = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_before = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="lte",
    )

    class Meta:
        model = Application
        fields = ["status", "created_after", "created_before"]
