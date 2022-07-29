from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from moc.lib.create_moc import CreateMoC
from hul.tasks import create_moc


class Command(BaseCommand):

    """ Description	"""

    help = 'Create MoC.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-y', '--year', nargs='?', default=timezone.now().year,
            type=int, help='Provide the year to generate moc',
        )

    def handle(self, *args, **options):
        print("======================= MoC Creation Initialized ======================= ")
        year = options["year"]
        if settings.CELERY_ENABLED:
            create_moc.delay(year)
        else:
            create_moc(year)

        print("======================= MoC Creation Succcessful ======================= ")
