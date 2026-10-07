from rest_framework import serializers

from .models import Candidate, Employer


class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            "id",
            "user",
            "full_name",
            "phone",
            "resume",
            "skills",
            "education",
            "experience_years",
            "expected_salary",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

    def validate_skills(self, value):
        if not isinstance(value, list) or not all(
            isinstance(s, str) for s in value
        ):
            raise serializers.ValidationError(
                'skills must be a list of strings, e.g. ["Python", "Django"].'
            )

        return [s.strip() for s in value if s.strip()]

    def validate_education(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "education must be a list of objects."
            )

        for entry in value:
            if not isinstance(entry, dict) or "degree" not in entry:
                raise serializers.ValidationError(
                    'each education entry needs at least a "degree" key.'
                )

        return value

    def validate_experience_years(self, value):
        if value < 0 or value > 60:
            raise serializers.ValidationError(
                "experience_years must be between 0 and 60."
            )

        return value

    def validate_expected_salary(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "expected_salary cannot be negative."
            )

        return value


class EmployerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = [
            "id",
            "user",
            "company_name",
            "domain",
            "industry",
            "company_size",
            "is_company_verified",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "is_company_verified",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

    def validate_company_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "company_name cannot be empty."
            )

        return value.strip()

    def validate_domain(self, value):
        if value and ("." not in value or " " in value):
            raise serializers.ValidationError(
                "domain must look like a real domain, e.g. zecpath.com."
            )

        return value.lower().strip()