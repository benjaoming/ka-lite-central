from django.contrib.auth.models import User

from centralserver.central.models import Organization
from fle_utils.config.models import Settings
from securesync.devices.models import Device, Zone


class FakeDeviceMixin(object):
    DEFAULTS = {
        'public_key': u'MIIBCgKCAQEAlbIPLnQH2dORFBK8i9x7/3E0DR571S01aP7M0TJD8vJf8OrgL8pnru3o2Jaoni1XasCZgizvM4GNImk9geqPP/sFkj0cf/MXSLr1VDKo1SoflST9yTbOi7tzVuhTeL4P3LJL6PO6iNiWkjAdqp9QX3mE/DHh/Q40G68meRw6dPDI4z8pyUcshOpxAHTSh2YQ39LJAxP7YS26yjDX/+9UNhetFxemMrBZO0UKtJYggPYRlMZmlTZLBU4ODMmK6MT26fB4DC4ChA3BD4OFiGDHI/iSy+iYJlcWaldbZtc+YfZlGhvsLnJlrp4WYykJSH5qeBuI7nZLWjYWWvMrDepXowIDAQAB',
        'private_key': u'-----BEGIN RSA PRIVATE KEY-----\nMIIEqQIBAAKCAQEAlbIPLnQH2dORFBK8i9x7/3E0DR571S01aP7M0TJD8vJf8Org\nL8pnru3o2Jaoni1XasCZgizvM4GNImk9geqPP/sFkj0cf/MXSLr1VDKo1SoflST9\nyTbOi7tzVuhTeL4P3LJL6PO6iNiWkjAdqp9QX3mE/DHh/Q40G68meRw6dPDI4z8p\nyUcshOpxAHTSh2YQ39LJAxP7YS26yjDX/+9UNhetFxemMrBZO0UKtJYggPYRlMZm\nlTZLBU4ODMmK6MT26fB4DC4ChA3BD4OFiGDHI/iSy+iYJlcWaldbZtc+YfZlGhvs\nLnJlrp4WYykJSH5qeBuI7nZLWjYWWvMrDepXowIDAQABAoIBAD8S/a6XGU/BA1ov\n4t4TkvO44TO96nOSTvTkl6x1v4e4dJBwhvHcGP/uIrRQFtA/TpwedxAQmuFa7vrW\n2SHKkX1l6Z0Kvt1yshblH8XQaq8WxqPzKDQGMdVSsHCoB7PScaCOR8nqGGjcyeTi\n/T0NT7JK46vX4N7dgttrE+WixOrtDOUJLX92tGSp8bZgg284fV053nJqYHHROpmZ\nCibM5HK8B/19ULCpglGQCUVmJPtRzNK1bE9OlB8P5aZzdEd82oC8TKfSGmByO1TI\nCat6x8e0hYVIDElYGdcW5CDAr6rbU0CXOxxQAz3gJFDe1/RbbGJEdjO3IulYbR4H\nBK+nGxECgYkA424wFuQGRAwig//SNasv5aIqz2qnczL5ob3MXCFR4aOMowS94qvd\neRG9McxgRwbEApOTMVMAUYlBMkKE//sBM9XWQ4q8igJ+TUlV8RRQ8AP6hMUhSXX0\nNeEECcauP4vI6hhsnTsG/OQ4pr/4bEewsyXFwPSGkh2v3O+fuc6A8RywQ3u6icc+\n9wJ5AKiACZmpSskyJgp+3X0jpYixb7pQ9gU6QpJmP9Z2DdUNnm0Y5tDjnaCd/Bvy\nmNuCWqNbYdlEYH32B3sCshzFCqQwkgSMOa84cHQHx4Nx7SG2fUp9w1ExvnMRzrnw\n3sjB3ptbNhk1yrkzhFbd6ZG4fsL5Mb0EurAFtQKBiFCUVc2GdQHfGsuR9DS3tnyx\n/GEI9NNIGFJKIQHzfENp4wZPQ8fwBMREmLfwJZyEtSYEi35KXi6FZugb0WuwzzhC\nZ2v+19Y+E+nmNeD4xcSEZFpuTeDtPd1pIDkmf85cBI+Mn88FfvBTHA9YrPgQXnba\nxzoaaSOUCR9Kd1kp5V2IQJtoVytBwPkCeFIDD6kkxuuqZu2Q1gkEgptHkZPjt/rP\nYnuTHNsrVowuNr/u8NkXEC+O9Zg8ub2NcsQzxCpVp4lnaDitFTf/h7Bmm4tvHNx1\n4fX3m1oU51ATXGQXVit8xK+JKU9DN4wLIGgJOwmGLwd5VZ5aIEb2v2vykgzn8l2e\nSQKBiQC7CJVToYSUWnDGwCRsF+fY9jUculveAQpVWj03nYBtBdTh2EWcvfoSjjfl\nmpzrraojpQlUhrbUf5MU1fD9+i6swrCCvfjXITG3c1bkkB5AaQW7NiPHvDRMuDpc\nHIQ+vqzdn4iUlt7KB5ChpnZMmgiOdCBM0vQsZlVCbp0ZNLqVYhFASQnWl6V9\n-----END RSA PRIVATE KEY-----\n'
    }

    @classmethod
    def setup_fake_device(cls, **kwargs):
        fields = FakeDeviceMixin.DEFAULTS.copy()
        fields.update(kwargs)

        Device.own_device = None

        Settings.set("public_key", fields.get('public_key'))
        Settings.set("private_key", fields.get('private_key'))

        Device.initialize_own_device()


class CreateAdminMixin(object):
    DEFAULTS = {
        'username': 'admin1',
        'password': 'password',
    }

    @classmethod
    def create_admin(cls, **kwargs):
        fields = CreateAdminMixin.DEFAULTS.copy()
        fields.update(kwargs)

        user = User.objects.create(**fields)
        user.real_password = fields['password']
        user.set_password(user.real_password)
        user.is_superuser = True
        user.save()

        return user


class CreateOrganizationMixin(object):
    DEFAULTS = {
        'name': 'org-1',
    }

    @classmethod
    def create_organization(cls, **kwargs):
        fields = CreateOrganizationMixin.DEFAULTS.copy()
        fields.update(kwargs)

        owner = fields.get('owner')
        if not owner:
            owner = User.objects.create(username='owner',
                                        password='password')

        fields['owner'] = owner

        members = fields.pop('members', [owner])

        org = Organization.objects.create(**fields)
        org.users.add(*members)
        org.save()

        return org


class CreateZoneMixin(CreateOrganizationMixin):
    DEFAULTS = {
        'name': 'zone-1'
    }

    @classmethod
    def create_zone(cls, **kwargs):
        fields = CreateZoneMixin.DEFAULTS.copy()
        fields.update(kwargs)

        orgs = fields.pop('organizations', None)
        if not orgs:
            orgs = [cls.create_organization()]

        zone = Zone.objects.create(**fields)
        zone.organization_set.add(*orgs)
        zone.save()

        return zone


class CentralServerMixins(CreateZoneMixin, CreateOrganizationMixin):
    pass
