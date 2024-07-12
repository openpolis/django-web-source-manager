from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from websourcemonitor.services.playwright import PlaywrightWrapper


class SourceType(models.Model):
    """the type of source, describes the kind of source the content is
    about"""

    name = models.CharField(
        max_length=250,
        verbose_name=_("Denominazione"),
    )
    slug = models.SlugField(
        max_length=250, verbose_name=_("Slug"),
        blank=True, null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'tipo di fonte'
        verbose_name_plural = 'tipi di fonte'


class APIException(BaseException):
    pass


class Content(models.Model):
    """a content on the web, identified by the URL and the XPATH expression"""

    STATUS_NOT_CHANGED = 0
    STATUS_CHANGED = 1
    STATUS_ERROR = 2
    STATUS_UPDATED = 3
    STATUS_SIGNALED = 4
    STATUS_CHOICES = (
        (STATUS_NOT_CHANGED, 'Immutato'),
        (STATUS_CHANGED, 'Cambiato'),
        (STATUS_ERROR, 'Errore rilevato'),
        (STATUS_UPDATED, 'Aggiornato alla destinazione'),
        (STATUS_SIGNALED, 'Errore segnalato'),
    )

    title = models.CharField(
        max_length=512,
        verbose_name=_("Denominazione della fonte"),
        help_text="""Indicare l'istituzione (es. Cons. Reg. Lazio)"""
    )
    source_type = models.ForeignKey(
        SourceType,
        verbose_name=_("Tipo di organizzazione"),
        on_delete=models.PROTECT
    )
    url = models.URLField(max_length=1024)
    op_url = models.URLField(
        blank=True, null=True,
        help_text="URL della pagina OP contenente le istituzioni"
    )
    selector = models.CharField(blank=True, max_length=512)
    content = models.TextField(
        blank=True, null=True,
        verbose_name=_("Contenuto significativo")
    )
    timeout = models.PositiveSmallIntegerField(
        blank=True, null=True,
    )
    notes = models.TextField(
        blank=True, null=True,
        verbose_name=_("Note")
    )
    is_verification_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Verification enabled"),
        help_text=_("Unset checkbox to disable verification")
    )
    verified_at = models.DateTimeField(
        blank=True, null=True,
        verbose_name=_("Last verification")
    )
    verification_status = models.IntegerField(
        null=True,
        choices=STATUS_CHOICES,
        verbose_name=_("Stato")
    )
    verification_error = models.TextField(
        blank=True, null=True,
        verbose_name=_("Errore")
    )
    use_cleaner = models.BooleanField(
        default=True,
        verbose_name=_("Utilizza cleaner")
    )
    use_proxy = models.BooleanField(
        default=True,
        verbose_name=_("Utilizza proxy IT")
    )

    class Meta:
        verbose_name = 'contenuto'
        verbose_name_plural = 'contenuti'

    def __str__(self):
        return self.title

    def get_live_content(self, playwright_wrapper=None, output_format='text'):

        if playwright_wrapper is None:
            pw = PlaywrightWrapper()
        else:
            pw = playwright_wrapper

        try:
            (resp_code, resp_content) = pw.get_live_content(self.url, self.selector, output_format)
            if playwright_wrapper is None:
                pw.stop()
            return resp_code, resp_content
        except Exception as e:
            pw.stop()
            raise e

    def verify(self, playwright_wrapper=None):

        (resp_code, resp_content) = self.get_live_content(playwright_wrapper=playwright_wrapper)

        if resp_code not in (200, 202):
            self.verification_status = Content.STATUS_ERROR
            self.verification_error = "ERRORE {0} ({1})".format(
                resp_code, resp_content
            )
        else:
            if resp_content != self.content:
                self.verification_status = self.STATUS_CHANGED
            else:
                self.verification_status = self.STATUS_NOT_CHANGED

            self.verification_error = None

        self.verified_at = timezone.now()
        self.save()

        return self.verification_status

    def update(self, playwright_wrapper=None):
        """updates db with live content; align verification status"""
        (resp_code, resp_content) = self.get_live_content(playwright_wrapper=playwright_wrapper)

        if resp_code not in (200, 202):
            self.verification_status = Content.STATUS_ERROR
            self.verification_error = "ERRORE {0} ({1})".format(
                resp_code, resp_content
            )
        else:
            self.content = resp_content
            self.verification_status = self.STATUS_UPDATED
            self.verification_error = None

        self.verified_at = timezone.now()
        self.save()

        return self.verification_status

    def reset(self):
        """resets content and status, restart from scratch"""
        self.content = None
        self.verification_status = None
        self.verification_error = None
        self.verified_at = None
        self.save()

    def is_verification_enabled_switch(self):
        """change the status of the is_verification_enabled flag"""
        self.is_verification_enabled = not self.is_verification_enabled
        self.save()
