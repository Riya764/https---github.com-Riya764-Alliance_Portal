from django.core.management.base import BaseCommand
from app.models import ShaktiEntrepreneur
from django.db import DatabaseError, transaction


class Command(BaseCommand):
    help = "will place a primary order for Distributor"

    def add_arguments(self, parser):
        # arguments to be passed here
        # parser.add_argument("order_id", nargs='+', type=int)
        pass

    def handle(self, *args, **options):

        shakti_obj = ChangeShakti()
        non_shakti, updated_shakti = shakti_obj.assign_username()
        print(non_shakti, updated_shakti)

        self.stdout.write(self.style.SUCCESS(
            'Successfully updated %s records and not updated %s ' % (updated_shakti, non_shakti)))


class ChangeShakti(object):
    shakti_users = []
    non_code_shakti = []
    updated_shakti = []

    def __init__(self):
        self.fetch_shakti()

    def fetch_shakti(self):
        self.shakti_users = ShaktiEntrepreneur.objects.all().order_by('id')

    def assign_username(self):
        for shakti in self.shakti_users:
            if shakti.code is not None:
                try:
                    with transaction.atomic():
                        shakti.user.username = shakti.code
                        shakti.user.save()
                        self.updated_shakti.append(shakti.user.id)
                except DatabaseError:
                    self.non_code_shakti.append(shakti.user.id)

        return self.non_code_shakti, self.updated_shakti
