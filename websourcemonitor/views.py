import difflib

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

from websourcemonitor.models import Content
from websourcemonitor.signal_form import SignalForm


# noinspection PyUnusedLocal
def diff(request, content_id):
    """
    generates a diff view, using difflib.HtmlDiff() method
    on live and stored html content

    each view means a request to the URI
    """

    obj = Content.objects.get(pk=content_id)
    (resp_code, resp_content) = obj.get_live_content()

    live = resp_content.splitlines(1)
    if obj.content:
        stored = obj.content.splitlines(1)
    else:
        stored = ''
    _diff = difflib.HtmlDiff().make_table(
        stored, live,
        fromdesc="Immagazzinato", todesc="Live",
        context=True, numlines=2
    )
    return render(
        request,
        "diff.html",
        context={'content': obj, 'diff': _diff}
    )


def signal(request, content_id):
    """
    generates a form containing the text area where a user can send
    a notification of an error in a content (false positives)

    :param request:
    :param content_id: the ID of the content
        """
    obj = Content.objects.get(pk=content_id)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        signal_form = SignalForm(request.POST)
        # check whether it's valid:
        if signal_form.is_valid():
            data = signal_form.cleaned_data
            obj.notes = data.get('message')
            obj.verification_status = Content.STATUS_SIGNALED
            obj.verified_at = timezone.now()
            obj.save()

            # redirect to a new URL:
            return HttpResponseRedirect(
                data.get('redirect_after_post')
                # reverse('admin:webapp_content_changelist')
            )

    # if a GET (or any other method) we'll create a blank form
    else:
        signal_form = SignalForm(
            initial={
                'message': obj.notes,
                'redirect_after_post': request.META['HTTP_REFERER']
            }
        )

    return render(
        request,
        "signal.html",
        context={'content': obj, 'signal_form': signal_form}
    )

