from __future__ import unicode_literals

from django.apps import AppConfig


class MocConfig(AppConfig):
    name = 'moc'

    def ready(self):
        _ = self.module
        import moc.signals
