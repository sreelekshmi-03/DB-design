from rest_framework import serializers

from .models import Job, Application


class JobSerializer(serializers.ModelSerializer):
    employer_name = serializers.CharField(
        source="employer.company_name",
        read_only=True,
    )

    class Meta:
        model = Job
        fields = [
            "id",
            "employer",
            "employer_name",
            "title",
            "description",
            "location",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "employer",
            "employer_name",
            "created_at",
            "updated_at",
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate.full_name",
        read_only=True,
    )
    job_title = serializers.CharField(
        source="job.title",
        read_only=True,
    )

    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "job_title",
            "candidate",
            "candidate_name",
            "status",
            "ats_score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "candidate",
            "candidate_name",
            "ats_score",
            "created_at",
            "updated_at",
        ]
