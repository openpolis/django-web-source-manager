# coding=utf-8
from django.core.management import BaseCommand

from websourcemonitor.models import Content


class Command(BaseCommand):
    help = 'List all contents in the DB ID, title and verification status'

    def handle(self, *args, **options):
        """Contains the command logic.
        Launch the scrapy crawl histadmin subprocess and log the output.

        :param args:
        :param options:
        :return:
        """

        self.setup_logger(__name__, formatter_key="simple", **options)

        for content in Content.objects.all():
            self.logger.info("{0.id} - \"{0.title}\" ({0.verification_status})".format(content))
