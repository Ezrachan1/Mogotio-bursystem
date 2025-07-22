from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import BursaryApplication, ApplicationStatusLog


@receiver(pre_save, sender=BursaryApplication)
def track_status_changes(sender, instance, **kwargs):
    """Track status changes for applications"""
    if instance.pk:  # If updating existing instance
        try:
            old_instance = BursaryApplication.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status has changed, we'll create a log after save
                instance._status_changed = True
                instance._old_status = old_instance.status
            else:
                instance._status_changed = False
        except BursaryApplication.DoesNotExist:
            instance._status_changed = False
    else:
        instance._status_changed = False


@receiver(post_save, sender=BursaryApplication)
def create_status_log(sender, instance, created, **kwargs):
    """Create status log when application status changes"""
    if created:
        # New application created
        ApplicationStatusLog.objects.create(
            application=instance,
            previous_status='',
            new_status=instance.status,
            changed_by=instance.applicant,
            comment='Application created'
        )
    elif hasattr(instance, '_status_changed') and instance._status_changed:
        # Status changed
        ApplicationStatusLog.objects.create(
            application=instance,
            previous_status=instance._old_status,
            new_status=instance.status,
            changed_by=getattr(instance, '_changed_by', None),
            comment=getattr(instance, '_status_change_comment', '')
        )