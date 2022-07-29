from django.core.management.base import BaseCommand, CommandError
from orders.lib.update_orders_moc import UpdateOrdersMoC


class Command(BaseCommand):
    help = '''Update mocs for existing orders'''

    def add_arguments(self, parser):
        parser.add_argument(
            '-t', '--type', nargs='?', default="primary",
            choices=["primary", "secondary"], help='Provide the order type : primary, secondary',
        )

    def handle(self, *args, **options):
        order_type = options["type"]

        if order_type == "primary":
            UpdateOrdersMoC.update_primary_orders()

        if order_type == "secondary":
            UpdateOrdersMoC.update_secondary_orders()

        self.stdout.write(self.style.SUCCESS(
            'Successfully updated mocs'))
