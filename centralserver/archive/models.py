"""
Archive models stored in a separate database:

#. Should not contain field references to the default database, data is
   maintained portable.
#. Retains its own unique reference fields, can be appended incrementally
#. Atomic "archive" command
"""

from django.db import models
from django.utils import timezone


class Device(models.Model):
    """
    Tracks a unique device, either registered to a User or through One-Click
    Registration (w/o details)
    """
    
    original_pk = models.PositiveIntegerField(unique=True)
    
    created = models.DateTimeField(_('created'))
    last_seen = models.DateTimeField(_('last seen'))


class Registration(models.Model):
    """
    Details of a registration, belonging to a set of devices. A device may be
    unregistered, so this is not the main point of entry.
    """

    original_pk = models.PositiveIntegerField(unique=True)

    created = models.DateTimeField(_('date created'), default=timezone.now)
    
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), blank=True)


class Facility(models.Model):

    original_pk = models.PositiveIntegerField(unique=True)

    devices = models.ManyToManyField(Device)
    
    name = models.CharField(verbose_name=_("Name"), help_text=_("(This is the name that learners/coaches will see when choosing their facility; it can be in the local language.)"), max_length=100)
    description = models.TextField(blank=True, verbose_name=_("Description"))
    address = models.CharField(verbose_name=_("Address"), help_text=_("(Please provide as detailed an address as possible.)"), max_length=400, blank=True)
    address_normalized = models.CharField(max_length=400, blank=True)
    latitude = models.FloatField(blank=True, verbose_name=_("Latitude"), null=True)
    longitude = models.FloatField(blank=True, verbose_name=_("Longitude"), null=True)
    zoom = models.FloatField(blank=True, verbose_name=_("Zoom"), null=True)
    contact_name = models.CharField(verbose_name=_("Contact Name"), help_text=_("(Who should we contact with any questions about this facility?)"), max_length=60, blank=True)
    contact_phone = models.CharField(max_length=60, verbose_name=_("Contact Phone"), blank=True)
    contact_email = models.EmailField(max_length=60, verbose_name=_("Contact Email"), blank=True)
    user_count = models.IntegerField(verbose_name=_("User Count"), help_text=_("(How many potential users do you estimate there are at this facility?)"), blank=True, null=True)


class FacilityGroup(models.Model):

    original_pk = models.PositiveIntegerField(unique=True)

    facility = models.ForeignKey(Facility, verbose_name=_("Facility"))
    name = models.CharField(max_length=30, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))


class FacilityAnoymizedUser(models.Model):
    """
    These objects are kept individual but the reference to the non-anonymous
    original user will eventually be removed.
    """

    original_pk = models.PositiveIntegerField(unique=True)


class SyncSessionSummary(models.Model):
    """
    Count how many times each device has sync'ed
    """

    device = models.ForeignKey(Device)

    last_updated_pivot = models.DateTimeField(
        help_text="When aggregating new data, this guides when data was last added",
    )

    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    
    count = models.PositiveIntegerField()

    # Summaries
    models_uploaded = models.IntegerField(default=0)
    models_downloaded = models.IntegerField(default=0)
    errors = models.IntegerField(default=0)
    closed = models.BooleanField(default=False)


class DeviceVersionSummary(models.Model):

    device = models.ForeignKey(Device)
    
    first_seen = models.DateTimeField(_('created'))
    last_seen = models.DateTimeField(_('last seen'))

    client_version = models.CharField(max_length=100, blank=True)
    client_os = models.CharField(max_length=200, blank=True)


class DeviceIPs(models.Model):
    """
    IPs seen for each device
    """
    
    device = models.ForeignKey(Device)
    ip = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ('device', 'ip')


class AttemptLog(models.Model):
    """
    Detailed instances of user exercise engagement.
    
    This table will be huge.
    """

    original_pk = models.PositiveIntegerField(unique=True)

    user = models.ForeignKey(FacilityAnoymizedUser, db_index=True)
    
    exercise_id = models.CharField(max_length=200, db_index=True)
    seed = models.IntegerField(default=0)
    answer_given = models.TextField(blank=True) # first answer given to the question
    points = models.IntegerField(default=0)
    correct = models.BooleanField(default=False) # indicates that the first answer given was correct
    complete = models.BooleanField(default=False) # indicates that the question was eventually answered correctly
    context_type = models.CharField(max_length=20, blank=True) # e.g. "exam", "quiz", "playlist", "topic"
    context_id = models.CharField(max_length=100, blank=True) # e.g. the exam ID, quiz ID, playlist ID, topic ID, etc
    language = models.CharField(max_length=8, blank=True)
    timestamp = models.DateTimeField() # time at which the question was first loaded (that led to the initial response)
    time_taken = models.IntegerField(blank=True, null=True) # time spent on exercise before initial response (in ms)
    version = models.CharField(blank=True, max_length=100) # the version of KA Lite at the time the answer was given
    response_log = models.TextField(default="[]")
    response_count = models.IntegerField(default=0)
    assessment_item_id = models.CharField(max_length=100, blank=True, default="")


class ContentLog(models.Model):

    original_pk = models.PositiveIntegerField(unique=True)
    user = models.ForeignKey(FacilityAnoymizedUser, blank=True, null=True, db_index=True)

    content_id = models.CharField(max_length=200, db_index=True)
    points = models.IntegerField(default=0)
    language = models.CharField(max_length=8, blank=True, null=True)
    complete = models.BooleanField(default=False)
    start_timestamp = models.DateTimeField(auto_now_add=True, editable=False)  # this must NOT be null
    completion_timestamp = models.DateTimeField(blank=True, null=True)
    completion_counter = models.IntegerField(blank=True, null=True)
    time_spent = models.FloatField(blank=True, null=True)
    progress_timestamp = models.DateTimeField(blank=True, null=True)
    latest_activity_timestamp = models.DateTimeField(blank=True, null=True)
    content_source = models.CharField(max_length=100, db_index=True, default="khan")
    content_kind = models.CharField(max_length=100, db_index=True)
    progress = models.FloatField(blank=True, null=True)
    views = models.IntegerField(blank=True, null=True)
    extra_fields = models.TextField(blank=True)


class UserLogSummary(models.Model):

    original_pk = models.PositiveIntegerField(unique=True)
    device = models.ForeignKey(Device, blank=False, null=False)
    user = models.ForeignKey(FacilityAnoymizedUser, blank=False, null=False, db_index=True)
    
    activity_type = models.IntegerField(blank=False, null=False)
    language = models.CharField(max_length=8, blank=True, null=True)
    start_datetime = models.DateTimeField(blank=False, null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)
    count = models.IntegerField(default=0, blank=False, null=False)
    total_seconds = models.IntegerField(default=0, blank=False, null=False)
    last_activity_datetime = models.DateTimeField(blank=True, null=True)


class ExerciseLog(models.Model):

    original_pk = models.PositiveIntegerField(unique=True)
    user = models.ForeignKey(FacilityAnoymizedUser, blank=True, null=True, db_index=True)

    exercise_id = models.CharField(max_length=200, db_index=True)
    streak_progress = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    language = models.CharField(max_length=8, blank=True, null=True)
    complete = models.BooleanField(default=False)
    struggling = models.BooleanField(default=False)
    attempts_before_completion = models.IntegerField(blank=True, null=True)
    completion_timestamp = models.DateTimeField(blank=True, null=True)
    completion_counter = models.IntegerField(blank=True, null=True)
    latest_activity_timestamp = models.DateTimeField(blank=True, null=True)


class VideoLog(models.Model):

    original_pk = models.PositiveIntegerField(unique=True)
    user = models.ForeignKey(FacilityAnoymizedUser, blank=True, null=True, db_index=True)

    video_id = models.CharField(max_length=200, db_index=True)
    youtube_id = models.CharField(max_length=20) # metadata only
    total_seconds_watched = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    language = models.CharField(max_length=8, blank=True, null=True)
    complete = models.BooleanField(default=False)
    completion_timestamp = models.DateTimeField(blank=True, null=True)
    completion_counter = models.IntegerField(blank=True, null=True)
    latest_activity_timestamp = models.DateTimeField(blank=True, null=True); latest_activity_timestamp.minversion="0.14.0"
