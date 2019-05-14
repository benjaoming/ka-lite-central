from datetime import datetime, timedelta
from collections_local_copy import OrderedDict

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from fle_utils.django_utils.classes import ExtendedModel
from securesync.models import Zone
from kalite.facility.models import FacilityGroup, Facility, FacilityUser


def get_or_create_user_profile(user):
    assert not user.is_anonymous(), "Should not be calling get_or_create_user_profile with an anonymous user."
    assert user.is_authenticated(), "Should not be calling get_or_create_user_profile with an anonymous user."

    return UserProfile.objects.get_or_create(user=user)[0]

class Organization(ExtendedModel):
    name = models.CharField(verbose_name="org name", max_length=100)
    description = models.TextField(help_text="<br/>How is this organization using KA Lite?", blank=True, )
    url = models.URLField(verbose_name="org URL", help_text="<br/>(optional)", blank=True)
    number = models.CharField(verbose_name="phone", max_length=100, blank=True)
    address = models.TextField(max_length=200, help_text="<br/>Street Address or PO Box, City/Town/Province, Postal Code", blank=True)
    country = models.CharField(max_length=100, blank=True)
    users = models.ManyToManyField(User)
    zones = models.ManyToManyField(Zone)
    owner = models.ForeignKey(User, related_name="owned_organizations", null=True)

    HEADLESS_ORG_NAME = "Unclaimed Networks"
    HEADLESS_ORG_PK = None  # keep the primary key of the headless org around, for efficiency
    HEADLESS_ORG_SAVE_FLAG = "internally_safe_headless_org_save"  # indicates safe save() call


    def add_zone(self, zone):
        return self.zones.add(zone)

    def get_zones(self):
        return self.zones.all().order_by("name")

    def add_member(self, user):
        return self.users.add(user)

    def get_members(self):
        return self.users.all()

    def is_member(self, user):
        return self.users.filter(pk=user.pk).count() > 0

    def __unicode__(self):
        return self.name

    def save(self, owner=None, *args, **kwargs):
        # backwards compatibility
        if not getattr(self, "owner_id", None):
            self.owner = owner
            assert self.owner or self.name == Organization.HEADLESS_ORG_NAME, "Organization must have an owner (save for the 'headless' org)"

        # Make org unique by name, for headless name only.
        #   So make sure that any save() call is coming either
        #   from a trusted source (passing HEADLESS_ORG_SAVE_FLAG),
        #   or doesn't overlap with our safe name
        if self.name == Organization.HEADLESS_ORG_NAME:
            if kwargs.get(Organization.HEADLESS_ORG_SAVE_FLAG, False):
                del kwargs[Organization.HEADLESS_ORG_SAVE_FLAG]  # don't pass it on, it's an error
            elif self.pk != Organization.get_or_create_headless_organization().pk:
                raise Exception("Cannot save to reserved organization name: %s" % Organization.HEADLESS_ORG_NAME)

        super(Organization, self).save(*args, **kwargs)


    @classmethod
    def from_zone(cls, zone):
        """
        Given a zone, figure out which organizations contain it.
        """
        return Organization.objects.filter(zones=zone)


    @classmethod
    def get_or_create_headless_organization(cls, refresh_zones=False):
        """
        Retrieve the organization encapsulating all headless zones.
        """
        if cls.HEADLESS_ORG_PK is not None:
            # Already exists and cached, just query fast and return
            headless_org = cls.objects.get(pk=cls.HEADLESS_ORG_PK)

        else:
            # Potentially inefficient query, so limit this to once per server thread
            # by caching the results.  Here, we've had a cache miss
            headless_orgs = cls.objects.filter(name=cls.HEADLESS_ORG_NAME)
            if not headless_orgs:
                # Cache miss because the org actually doesn't exist.  Create it!
                headless_org = Organization(name=cls.HEADLESS_ORG_NAME)
                headless_org.save(**({cls.HEADLESS_ORG_SAVE_FLAG: True}))
                cls.HEADLESS_ORG_PK = headless_org.pk

            else:
                # Cache miss because it's the first relevant query since this thread started.
                assert len(headless_orgs) == 1, "Cannot have multiple HEADLESS ZONE organizations"
                cls.HEADLESS_ORG_PK = headless_orgs[0].pk
                headless_org = headless_orgs[0]

        # TODO(bcipolli): remove this code!
        #
        # In the future, when we self-register headless zones, we'll
        #    add them directly to the headless organization.
        #    For now, we'll have to do an exhaustive search.
        if refresh_zones:
            headless_org.zones.add(*Zone.get_headless_zones())

        return headless_org


class UserProfile(ExtendedModel):
    user = models.OneToOneField(User)

    def __unicode__(self):
        return self.user.username

    def get_organizations(self):
        """
        Return all organizations that this user manages.

        If this user is a super-user, then the headless org will be appended at the end.
        """
        orgs = OrderedDict()  # no dictionary comprehensions, so have to loop
        for org in self.user.organization_set.all().order_by("name"):  # add in order queries (alphabetical?)
            orgs[org.pk] = org

        # Add a headless organization for superusers, containing
        #   any headless zones.
        # Make sure this is at the END of the list, so it is clearly special.
        if self.user.is_superuser:
            headless_org = Organization.get_or_create_headless_organization(refresh_zones=True)
            orgs[headless_org.pk] = headless_org

        return orgs

    def has_permission_for_object(self, object):

        return True

        # super users have access to every object
        if self.user.is_superuser:
            return True

        # we can only grant permissions for syncable models (might be good to raise an exception here instead)
        if not hasattr(object, "get_zone"):
            return False

        # allow access if the object's zone belongs to an org of which the user is a member
        if isinstance(object, Zone):
            zone = object
        else:
            zone = object.get_zone()
        for org in Organization.from_zone(zone):
            if org.is_member(self.user):
                return True

        # if we didn't find any reason to grant access -- don't!
        return False


class OrganizationInvitation(ExtendedModel):
    email_to_invite = models.EmailField(verbose_name="Email of invitee", max_length=75)
    invited_by = models.ForeignKey(User)
    organization = models.ForeignKey(Organization, related_name="invitations")

    class Meta:
        unique_together = ('email_to_invite', 'organization')

    def save(self, *args, **kwargs):
        if self.invited_by and self.organization not in self.invited_by.organization_set.all():
            raise PermissionDenied("User %s does not have permissions to invite people on this organization." % self.invited_by)
        super(OrganizationInvitation, self).save(*args, **kwargs)

    def send(self, request):
        to_email = self.email_to_invite
        sender = settings.CENTRAL_FROM_EMAIL
        cdict = {
            'invited_email': to_email,
            'organization': self.organization,
            'invited_by': self.invited_by,
            'central_server_host': request.get_host(),  # for central server actions, determine DYNAMICALLY to be safe
        }
        # Invite an existing user
        if User.objects.filter(email=to_email).count() > 0:
            subject = render_to_string('central/org_invite_email_subject.txt', cdict, context_instance=RequestContext(request))
            body = render_to_string('central/org_invite_email.txt', cdict, context_instance=RequestContext(request))
        # Invite an unregistered user
        else:
            subject = render_to_string('central/central_invite_email_subject.txt', cdict, context_instance=RequestContext(request))
            body = render_to_string('central/central_invite_email.txt', cdict, context_instance=RequestContext(request))
        send_mail(subject, body, sender, [to_email], fail_silently=False)


class DeletionRecord(ExtendedModel):

    organization = models.ForeignKey(Organization)
    deleter = models.ForeignKey(User, related_name="deletion_actor")
    deleted_user = models.ForeignKey(User, related_name="deletion_recipient", blank=True, null=True)
    deleted_invite = models.ForeignKey(OrganizationInvitation, blank=True, null=True)


class CSVJob(models.Model):
    
    # Can you make a kind of ENUM list in Python, where each item also has
    # a string label associated with it? :)
    (
        USERS,
        ATTEMPTS,
        EXERCISES,
        RATINGS,
        DEVICES,
    ) = REPORT_TYPE_ENUMS = range(0, 5) 
    
    REPORT_TYPE_CHOICES = zip(
        REPORT_TYPE_ENUMS,
        (
            "User log",
            "Attempt log",
            "Exercise log",
            "Ratings",
            "Device log"
        ),
    )
    
    owner = models.ForeignKey(
        User,
        help_text=_("Owner having rights to access this job at its creation time")
    )
    zone = models.ForeignKey(Zone)
    facility = models.ForeignKey(Facility, null=True, blank=True)
    facility_group = models.ForeignKey(FacilityGroup, null=True, blank=True)
    
    report_type = models.PositiveSmallIntegerField(
        default=0,
        choices=REPORT_TYPE_CHOICES,
    )

    finished = models.BooleanField(default=False)
    
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True,)

    csv_file = models.FileField(null=True, blank=True, upload_to='csv_reports/')

    def set_expiry(self):
        """
        Sets the expiry to 14 days after the last modification (assumed when the
        job result was ready)
        """
        self.expires_at = self.modified + timedelta(days=14)
        self.save()

    def get_queryset(self):
        
        if self.report_type == CSVJob.USERS:
            
            # COPY-PAST, NEED TO FIX.
            zone_id = self.zone
            facility_id = self.facility
            group_id = self.facility_group
        
            # They must have a zone_id, and may have a facility_id and group_id.
            # Try to filter from most specific, to least
            if group_id:
                facility_user_objects = FacilityUser.objects.filter(group__id=group_id)
            elif facility_id:
                facility_user_objects = FacilityUser.objects.filter(facility__id=facility_id)
            elif zone_id:
                facility_user_objects = FacilityUser.objects.by_zone(get_object_or_None(Zone, id=zone_id))
            else:
                facility_user_objects = FacilityUser.objects.all()
