from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_admin_row_actions import AdminRowActionsMixin
from django_object_actions import DjangoObjectActions

from . import jobs
from .filters import ErrorCodeFilter
from .models import Content, SourceType


class ContentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # noinspection PyArgumentList
        super(ContentForm, self).__init__(*args, **kwargs)
        if self.instance.content:
            self.initial['content'] = self.instance.content.replace('\n', '<br/>')


class ContentAdmin(DjangoObjectActions, AdminRowActionsMixin, admin.ModelAdmin):
    form = ContentForm
    list_display = (
        '_linked_title',
        'verified_at', '_status_and_message',
        'is_verification_enabled', 'use_proxy', 'use_cleaner'
    )
    search_fields = ('title', 'notes', 'verification_error', 'verification_status', 'url')
    list_filter = (
        'verification_status', ErrorCodeFilter,
        'source_type', 'is_verification_enabled',
        'use_cleaner', 'use_proxy'
    )
    fieldsets = (
        (None, {
            'fields': (
                'title', 'source_type', 'timeout', 'browser','scraping_class', 'notes',
                'op_url', 'url', 'selector',
                'use_cleaner', 'use_proxy',
                'content'
            ),
        }),
        ('Verification', {
            'fields': ('is_verification_enabled', 'verified_at', 'verification_status', 'verification_error')
        })
    )
    readonly_fields = (
        'content', 'verified_at', 'verification_status', 'verification_error'
    )

    def _linked_title(self, obj):
        return mark_safe(
            '{o.title} <a href="{o.url}" target="_blank"><img '
            'src="/static/images/extlink.gif" alt="vai" title="vai alla '
            'url: {o.url}"</a>'.format(o=obj)
        )
    _linked_title.short_description = 'Identificativo della URL'

    def _status_and_message(self, obj):
        status = obj.verification_status
        msg = obj.get_verification_status_display()
        if msg is not None:
            msg = msg.upper()
        if obj.verification_status == 1:
            msg += mark_safe(
                ' <a href="/websourcemonitor/diff/{0}" target="_blank"><img '
                'src="/static/images/extlink.gif" alt="vai"/> '
                'visualizza le differenze</a>'.format(obj.id)
            )
        if obj.verification_status == 2:
            msg = obj.verification_error

        return mark_safe(f"{status} - {msg}")
    _status_and_message.short_description = 'Status'

    # list actions on many objects (checkbox)
    def verify_queryset(self, request, queryset):
        try:
            if settings.USE_RQ:
                jobs.verify_contents.delay(queryset)
                self.message_user(request, "Contenuti verificati (coda)")
            else:
                jobs.verify_contents(queryset)
                self.message_user(request, "Contenuti verificati")
        except Exception as err:
            self.message_user(
                request, f"Errore durante la verifica dei contenuti: {err}",
                level=messages.ERROR
            )
    verify_queryset.short_description = "Verifica differenze sui siti live"

    def update_queryset(self, request, queryset):
        try:
            if settings.USE_RQ:
                jobs.update_contents.delay(queryset)
                self.message_user(request, "Contenuti aggiornati (coda)")
            else:
                jobs.update_contents(queryset)
                self.message_user(request, "Contenuti aggiornati")
        except Exception as err:
            self.message_user(
                request, f"Errore durante l'aggiornamento dei contenuti: {err}",
                level=messages.ERROR
            )
    update_queryset.short_description = "Aggiorna i contenuti"

    def disable_objects(self, request, objects):  # noqa
        for obj in objects:
            obj.is_verification_enabled = False
            obj.save()
    disable_objects.short_description = "Disabilita verifica"

    def enable_objects(self, request, objects):  # noqa
        for obj in objects:
            obj.is_verification_enabled = True
            obj.save()
    enable_objects.short_description = "Abilita verifica"

    change_form_template = "admin/content_change_form.html"
    save_on_top = True

    actions = [verify_queryset, update_queryset, disable_objects, enable_objects]

    def get_row_actions(self, obj):
        row_actions = [
            {
                'label': 'Verifica contenuto',
                'action': 'verify',
                'tooltip': 'Verifica il contenuto della fonte',
                'enabled': True
            },
            {
                'label': 'Abilita/Disabilita verifica',
                'action': 'is_verification_enabled_switch',
                'tooltip': 'Abilita o disabilita la verifica',
                'enabled': True
            },
            {
                'label': 'OP Aggiornato',
                'action': 'update',
                'tooltip': 'Segnala che la fonte è stata aggiornata in OP',
                'enabled': True
            },
            {
                'label': 'Segnala Errore',
                'url': '/signal/{0}'.format(obj.pk),
                'target': '_blank',
                'tooltip': 'Segnala falsi positivi o altri errori',
                'enabled': True
            },
            {
                'label': 'Reset',
                'action': 'reset',
                'tooltip': 'Svuota il contenuto, si riparte da zero',
                'enabled': True
            },

        ]
        row_actions += super(ContentAdmin, self).get_row_actions(obj)
        return row_actions

    def response_change(self, request, obj):
        if "_verify-content" in request.POST:
            try:
                obj.verify()
                msg = format_html(
                    f"Il {self.opts.verbose_name} “{obj}” è stato verificato e salvato."
                )
                self.message_user(request, msg, messages.SUCCESS)
            except Exception as err:
                self.message_user(
                    request, f"Errore durante la verifica del contenuto: {err}",
                    level=messages.ERROR
                )
        if "_reset-content" in request.POST:
            try:
                obj.reset()
                msg = format_html(
                    f"Il {self.opts.verbose_name} “{obj}” è stato resettato."
                )
                self.message_user(request, msg, messages.SUCCESS)
            except Exception as err:
                self.message_user(
                    request, f"Errore durante il reset del contenuto: {err}",
                    level=messages.ERROR
                )
        if "_markcorrected-content" in request.POST:
            try:
                obj.update()
                msg = format_html(
                    f"Il {self.opts.verbose_name} “{obj}” è stato segnato come corretto in OP."
                )
                self.message_user(request, msg, messages.SUCCESS)
            except Exception as err:
                self.message_user(
                    request, f"Errore durante l'operazione: {err}",
                    level=messages.ERROR
                )
        return self.response_post_save_change(request, obj, stayhere=True)

    def response_post_save_change(self, request, obj, stayhere=False):
        if stayhere:
            post_url = reverse('admin:%s_%s_change' % (self.opts.app_label,  self.opts.model_name),  args=[obj.id])
            return HttpResponseRedirect(post_url)
        else:
            super().response_post_save_change(request, obj)


admin.site.register(Content, ContentAdmin)
admin.site.register(SourceType)
