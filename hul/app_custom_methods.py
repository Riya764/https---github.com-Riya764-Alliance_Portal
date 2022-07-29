'''application custom method'''
from datetime import datetime, timedelta
from oauth2_provider.models import Application, AccessToken, RefreshToken
from oauthlib.oauth2.rfc6749.tokens import random_token_generator
from hul.constants import OAUTH_EXPIRY_SECONDS


class AppCustomMethods():
    '''class for common functions in app.api file'''
    @classmethod
    def create_access_token(cls, user, request, application_name):
        ''' API for create access token funcion'''
        application = Application.objects.get(name=application_name)
        expires = datetime.now() + timedelta(seconds=OAUTH_EXPIRY_SECONDS)
        access_token = AccessToken.objects.create(user=user,
                                                  token=random_token_generator(
                                                      request),
                                                  application=application,
                                                  expires=expires, scope='read write')
        RefreshToken.objects.create(user=user,
                                    token=random_token_generator(request),
                                    access_token=access_token,
                                    application=application)
        return access_token.token
