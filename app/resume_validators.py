import hashlib

from django.conf import settings
from django.core.exceptions import ValidationError


# Magic bytes (file signatures) for each allowed type.
MAGIC_SIGNATURES = {
    "pdf": [b"%PDF"],
    "doc": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],
    "docx": [b"PK\x03\x04"],
}


def get_extension(filename: str) -> str:
    return (
        filename.rsplit(".", 1)[-1].lower()
        if "." in filename
        else ""
    )


def validate_resume_file(uploaded_file):
    """
    Validate resume extension, content type, size,
    and file signature before saving.
    """

    ext = get_extension(uploaded_file.name)

    allowed_ext = getattr(
        settings,
        "RESUME_ALLOWED_EXTENSIONS",
        ["pdf", "doc", "docx"],
    )

    if ext not in allowed_ext:
        raise ValidationError(
            f"Unsupported file type '.{ext}'. "
            f"Allowed: {', '.join(allowed_ext)}."
        )

    allowed_ct = getattr(
        settings,
        "RESUME_ALLOWED_CONTENT_TYPES",
        [],
    )

    if allowed_ct and uploaded_file.content_type not in allowed_ct:
        raise ValidationError(
            f"Unexpected content type "
            f"'{uploaded_file.content_type}'."
        )

    max_mb = getattr(
        settings,
        "RESUME_MAX_SIZE_MB",
        5,
    )

    if uploaded_file.size > max_mb * 1024 * 1024:
        raise ValidationError(
            f"File too large "
            f"({uploaded_file.size / 1_048_576:.1f} MB). "
            f"Max is {max_mb} MB."
        )

    # Read the first 8 bytes without consuming the file.
    header = uploaded_file.read(8)

    # Reset the file pointer so Django can save the complete file.
    uploaded_file.seek(0)

    expected_signatures = MAGIC_SIGNATURES.get(
        ext,
        [],
    )

    if expected_signatures and not any(
        header.startswith(signature)
        for signature in expected_signatures
    ):
        raise ValidationError(
            f"This file's content doesn't match a real "
            f".{ext} file. It may be renamed or corrupted. "
            "Please upload a genuine PDF/DOC/DOCX."
        )


def compute_file_hash(uploaded_file) -> str:
    """
    Calculate SHA-256 hash of the uploaded file.

    Used for duplicate resume detection.
    """

    hasher = hashlib.sha256()

    for chunk in uploaded_file.chunks():
        hasher.update(chunk)

    uploaded_file.seek(0)

    return hasher.hexdigest()