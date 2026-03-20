from django import forms


class SubscribeForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "you@example.com",
        }),
    )
    def clean_email(self):
        return self.cleaned_data["email"].lower()

    # Honeypot field — should remain empty. Bots tend to fill it in.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "autocomplete": "off",
            "tabindex": "-1",
            "style": "position:absolute;left:-9999px;",
        }),
    )
