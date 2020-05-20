from django.core.management.base import BaseCommand

from ... import models


class Command(BaseCommand):
    help = (
        "Syncs all the various tables of kalite (central server) to a separate "
        "archive database"
    )

    def handle(self, *args, **options):
        pass

