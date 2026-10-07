"""
Resume upload API - the Day 12 main deliverable.

One endpoint handles both "first upload" and "replace existing resume",
since a Candidate only ever has one resume at a time (profile integration:
it's a field on Candidate, not a separate gallery of files).
"""
import os
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .middleware import IsCandidate
from .resume_validators import validate_resume_file, compute_file_hash
from django.core.exceptions import ValidationError as DjangoValidationError
class ResumeUploadView(APIView):
    """
    POST   /api/profile/candidate/resume/   -> upload or replace your resume
    DELETE /api/profile/candidate/resume/   -> remove your resume entirely
    Candidate-only, always acts on request.user.candidate_profile - there's
    no id in the URL, so there's no way to overwrite someone else's resume.
    """
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        candidate = request.user.candidate_profile
        uploaded_file = request.FILES.get("resume")

        if not uploaded_file:
            return Response({"detail": "No file provided. Use form field name 'resume'."},
                             status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_resume_file(uploaded_file)
        except DjangoValidationError as e:
            return Response({"detail": e.message if hasattr(e, "message") else str(e)},
                             status=status.HTTP_400_BAD_REQUEST)

        new_hash = compute_file_hash(uploaded_file)

        # Duplicate handling: if the uploaded content is byte-identical to
        # what's already on file, don't write a second copy or bump the
        # timestamp - just tell the candidate nothing changed.
        if candidate.resume and candidate.resume_sha256 == new_hash:
            return Response(
                {"detail": "This is the same resume you already have on file - no changes made."},
                status=status.HTTP_200_OK,
            )

        # Resume replacement: delete the old file from disk before saving the
        # new one, so replacing a resume doesn't silently leak orphaned files
        # into /media/ forever.
        old_file = candidate.resume
        if old_file:
            old_path = old_file.path
            if os.path.isfile(old_path):
                os.remove(old_path)

        candidate.resume = uploaded_file
        candidate.resume_original_name = uploaded_file.name
        candidate.resume_sha256 = new_hash
        candidate.resume_uploaded_at = timezone.now()
        candidate.save(update_fields=[
            "resume", "resume_original_name", "resume_sha256", "resume_uploaded_at",
        ])

        return Response({
            "detail": "Resume uploaded successfully.",
            "resume_url": request.build_absolute_uri(candidate.resume.url),
            "original_name": candidate.resume_original_name,
            "uploaded_at": candidate.resume_uploaded_at,
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        candidate = request.user.candidate_profile
        if candidate.resume:
            if os.path.isfile(candidate.resume.path):
                os.remove(candidate.resume.path)
            candidate.resume.delete(save=False)
            candidate.resume_original_name = ""
            candidate.resume_sha256 = ""
            candidate.resume_uploaded_at = None
            candidate.save(update_fields=[
                "resume", "resume_original_name", "resume_sha256", "resume_uploaded_at",
            ])
        return Response({"detail": "Resume removed."}, status=status.HTTP_204_NO_CONTENT)