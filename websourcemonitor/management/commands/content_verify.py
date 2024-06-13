import difflib

from django.core import management
from django.core.management import BaseCommand
from django.utils.timezone import now
from websourcemonitor.models import Content


class Command(BaseCommand):
    help = "Verify content of specified URI's ids or all"

    def add_arguments(self, parser):
        parser.add_argument('ids', nargs='*', type=int)

        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dryrun',
            default=False,
            help='Execute a dry run: no db is written, no notification sent.',
        )
        parser.add_argument(
            '--content',
            action='store_true',
            dest='showmeat',
            default=False,
            help='Show extracted text',
        )
        parser.add_argument(
            '--diff',
            action='store_true',
            dest='showdiff',
            default=False,
            help='Show diff code.',
        )
        parser.add_argument(
            '--offset',
            type=int,
            dest='offset',
            default=0,
            help='Force offset <> 0',
        )
        parser.add_argument(
            '--limit',
            type=int,
            dest='limit',
            default=0,
            help='Force offset <> 0',
        )
        parser.add_argument(
            '--notify',
            action='store_true',
            dest='notify',
            default=False,
            help='Notify changes to registered recipients or channels',
        )
        parser.add_argument(
            '--notification-method',
            dest='notification_method',
            default='slack',
            help='What method to use for notification: slack|email|both',
        )

    def handle(self, *args, **options):
        self.setup_logger(__name__, formatter_key="simple", **options)

        offset = options['offset']
        limit = options['limit']
        ids = options.get('ids', [])

        if len(ids) == 0:
            if limit > 0:
                contents = Content.objects.all()[
                           offset:(offset + limit)]
            else:
                contents = Content.objects.all()[offset:]
        else:
            contents = Content.objects.filter(id__in=ids)

        contents = contents.filter(is_verification_enabled=True)

        if len(contents) == 0:
            self.logger.info("no content to check this time")

        for cnt, content in enumerate(contents):
            err_msg = ''
            try:
                _ = content.verify(options['dryrun'])
            except IOError:
                err_msg = "Url non leggibile: {0}".format(content.url)
            except Exception as e:
                err_msg = "Errore sconosciuto: {0}".format(e)
            finally:
                if err_msg != '':
                    if options['dryrun'] is False:
                        content.verification_status = Content.STATUS_ERROR
                        content.verification_error = err_msg
                        content.verified_at = now()
                        content.save()
                    self.logger.warning("{0}/{1} - {2} while processing {3} (id: {4})".format(
                        cnt + 1, len(contents), err_msg, content.title, content.id
                    ))
                else:
                    if content.verification_error:
                        status = content.verification_error
                    else:
                        status = content.get_verification_status_display().upper()
                    self.logger.info(
                        "{0}/{1} - {2} (id: {4}) - {3}".format(
                            cnt + 1, len(contents), content.title,
                            status,
                            content.id,
                        )
                    )
                    if options['showmeat'] is True:
                        self.logger.info("Contenuto significativo: {0}".format(content.get_live_content()))
                    if options['showdiff'] is True:
                        live = content.get_live_content().splitlines(1)
                        stored = content.meat.splitlines(1)
                        diff = difflib.ndiff(live, stored)
                        self.logger.info("".join(diff))

        if options['notify'] and not options['dryrun']:
            verbosity = int(options.get("verbosity", 1))
            management.call_command(
                'notify',
                verbosity=verbosity,
                notification_method=options['notification_method'],
                stdout=self.stdout,
            )
