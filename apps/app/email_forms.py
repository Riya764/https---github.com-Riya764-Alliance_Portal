from django import forms
from django.template import loader
from django.utils.encoding import force_bytes
from django.core.mail.message import EmailMessage
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from hul.constants import RESET_EMAIL_SUBJECT, FROM_EMAIL


class HTMLPasswordResetForm(forms.Form):
    '''Html reset password form'''
    email = forms.EmailField(label=_("Email"), max_length=254)

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator, request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        email = self.cleaned_data["email"]

        user = get_user_model()
        active_users = user.objects.filter(
            email__iexact=email, is_active=True)

        for user in active_users:
            # Make sure that no email is sent to a user that actually has
            # a password marked as unusable
            if not user.has_usable_password():
                continue
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            context = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
            }
            subject = loader.render_to_string(subject_template_name, context)
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, context)

            (RESET_EMAIL_SUBJECT,
                               email, FROM_EMAIL, [user.email])
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send()
