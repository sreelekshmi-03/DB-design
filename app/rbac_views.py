from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Job, Application, Candidate, User
from .middleware import (
    IsAdmin,
    IsEmployer,
    IsCandidate,
    IsOwnerEmployer,
    IsOwnerCandidate,
)
# Serializers

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "description",
            "location",
            "status",
            "employer",
            "created_at",
        ]
        read_only_fields = ["employer", "created_at"]


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "candidate",
            "status",
            "ats_score",
            "created_at",
        ]
        read_only_fields = [
            "candidate",
            "status",
            "ats_score",
            "created_at",
        ]
# Jobs
class JobListCreateView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    queryset = Job.objects.filter(status=Job.Status.OPEN)   
    def get_permissions(self):
        if self.request.method == "POST":
            return [
                permissions.IsAuthenticated(),
                IsEmployer(),
            ]
        return [permissions.IsAuthenticated()]
    def perform_create(self, serializer):
        serializer.save(
            employer=self.request.user.employer_profile
        )
class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobSerializer
    queryset = Job.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
        IsOwnerEmployer,
    ]
# Applications
class ApplicationCreateView(generics.CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsCandidate,
    ]
    def perform_create(self, serializer):
        serializer.save(
            candidate=self.request.user.candidate_profile
        )
class MyApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsCandidate,
    ]
    def get_queryset(self):
        return Application.objects.filter(
            candidate=self.request.user.candidate_profile
        )
class ApplicationDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ApplicationSerializer
    queryset = Application.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
        IsOwnerCandidate,
    ]
# Admin control
class VerifyUserView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdmin,
    ]
    def post(self, request, user_id):
        try:
            target = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        target.is_verified = True
        target.save(update_fields=["is_verified"])

        return Response(
            {
                "detail": f"{target.email} marked as verified."
            },
            status=status.HTTP_200_OK,
        )