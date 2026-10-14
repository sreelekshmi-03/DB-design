
import django_filters

from app.models import Job, Application


class JobFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Job.Status.choices)
    location = django_filters.CharFilter(lookup_expr="icontains")
    created_after = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Job
        fields = ["status", "location", "created_after", "created_before"]


class ApplicationFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Application.Status.choices)
    created_after = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Application
        fields = ["status", "created_after", "created_before"]