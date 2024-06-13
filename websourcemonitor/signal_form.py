from django import forms


class SignalForm(forms.Form):
    redirect_after_post = forms.CharField(widget=forms.HiddenInput)
    message = forms.CharField(widget=forms.Textarea, label='Messaggio')
