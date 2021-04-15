from django import forms

from .models import UserProfile


class ProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = (
            'external_id',
            'name'
        )
        widgets = {
            'name': forms.TextInput
        }
