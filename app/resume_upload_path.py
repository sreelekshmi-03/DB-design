import uuid
from app.resume_validators import get_extension
def resume_upload_path(instance, filename):
    ext = get_extension(filename)
    new_name = f"{uuid.uuid4().hex}.{ext}"
    return f"resumes/candidate_{instance.user_id}/{new_name}"