from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User,Employer,Candidate
@receiver(post_save,sender=User)
def create_role_profile(sender,instance:User,created,**kwargs):
    if not created:
        return
    if instance.role==User.Role.EMPLOYER:
        Employer.objects.get_or_create(user=instance)
    elif instance.role ==User.Role.CANDIDATE:
        Candidate.objects.get_or_create(user=instance)
@receiver(post_save,sender=User)
def sync_role_profile(sender,instance:User,created,**kwargs):
    if created:
        return
    if instance.role ==User.Role.EMPLOYER and not hasattr(instance,"employer_profile"):
        Employer.objects.get_or_create(user=instance)
    elif instance.role==User.Role.CANDIDATE and not hasattr(instance,"candidate_profile"):
        Candidate.objects.get_or_create(user=instance)