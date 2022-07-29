''' Api.py'''
import random
from datetime import datetime, timedelta
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.template.context import Context
from django.template.loader import render_to_string
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework import permissions

from django.core.mail.message import EmailMessage

from oauth2_provider.models import AccessToken

from hul.app_custom_methods import AppCustomMethods
from hul.utility import HulUtility
from hul.messages import Messages
from hul.choices import OtpStatusType
from hul.constants import (EMAIL, USERNAME, PASSWORD, ECOMM_APPLICATION_NAME,
                           ACCESSTOKEN, SUCCESS_MESSAGE_KEY, MESSAGE_KEY, OTP_EXPIRE_TIME,
                           OTP_KEY, FROM_EMAIL, HTTP_USER_ERROR, HTTP_INVALID_TOKEN,
                           TOKEN_KEY, HTTP_INVALID_OTP, OLD_PASSWORD, NEW_PASSWORD,
                           HTTP_INVALID_PASSWORD, SHAKTI_ENTERPERNEUR_LIST_SIZE,
                           ALLIANCE_PARTNER_LIST_SIZE, USERTYPE, SUBJECT_PREFIX, RESET_EMAIL_SUBJECT)
from app.models import (User, RegionalSalesPromoter, ForgotPassword,
                        ShaktiEntrepreneur, RegionalDistributor, AlliancePartner)
from app.serializers import (UserSerializer, AccessTokenSerializer,
                             ShaktiEntrepreneurSerializer, AlliancePartnerSerializer)
from app.permissions import IsOwnerOrReadOnly
from job.models import Email
# =========================================================================
# User Sign In class
# Required Parameters:- email, password
# =========================================================================


class Login(generics.RetrieveAPIView):
    '''
    API to return User Info.
    '''
    serializer_class = UserSerializer

    def post(self, request):
        '''
        api to login alliance user only
        '''
        user = authenticate(username=self.request.data.get(USERNAME, None),
                            password=self.request.data.get(PASSWORD, None))
        if user:
            response = {}
            response_data = {}
            access = AppCustomMethods()
            alliance = RegionalSalesPromoter.objects.filter(
                user_id=user.pk, is_active=True)
            shakti_enterpreneur = ShaktiEntrepreneur.objects.filter(
                user_id=user.pk, is_active=True)
            if alliance or shakti_enterpreneur:
                if alliance:
                    user_type = 1
                else:
                    user_type = 2

                access_token = access.create_access_token(user, request,
                                                          ECOMM_APPLICATION_NAME)
                serializer = UserSerializer(user)
                response_data = serializer.data
                response_data[ACCESSTOKEN] = access_token
                response_data[USERTYPE] = user_type
                response = HulUtility.data_wrapper(response_data, status.HTTP_200_OK,
                                                   SUCCESS_MESSAGE_KEY)
                return Response(response, status=status.HTTP_200_OK)
            else:
                response_data = HulUtility.data_wrapper(
                    None, status.HTTP_204_NO_CONTENT)
                response_data[MESSAGE_KEY] = Messages.NOT_AUTHENTICATED
        else:
            response_data = HulUtility.data_wrapper(
                None, status.HTTP_204_NO_CONTENT)
            response_data[MESSAGE_KEY] = Messages.WRONG_USERNAME
        return Response(response_data, status=status.HTTP_200_OK)

# =========================================================================
# User SignOut Using UserToken
# =========================================================================


class SignOut(generics.DestroyAPIView):
    '''
    API for Expire Access Token to Sign out the User
    '''
    serializer_class = AccessTokenSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)

    @classmethod
    def put(cls, request):
        'for handling put request of signout service'
        token = request.META['HTTP_AUTHORIZATION']
        lst_token = token.split(' ')
        access_token = get_object_or_404(AccessToken, token=lst_token[1])
        access_token.expires = timezone.now()
        access_token.save()
        response = ""
        response_data = HulUtility.data_wrapper(response,
                                                status.HTTP_200_OK,
                                                message=Messages.SIGNOUT_SUCCESS)
        return Response(response_data, status=status.HTTP_200_OK)


# =========================================================================
# Forgot password API to send OTP on mail using jobs
# =========================================================================
class SetForgotPassword(generics.RetrieveAPIView):
    '''
    API for Forgot password to send OTP on mail
    '''
    DIGITS = 4

    @classmethod
    def post(cls, request):
        ''' POST Request only '''
        email = request.data.get(EMAIL, None)
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        # import pdb; pdb.set_trace()
        response_data = {}
        if user:
            lower = 10 ** (cls.DIGITS - 1)
            upper = 10 ** cls.DIGITS - 1
            otp_value = random.randint(lower, upper)
            otp_details = ForgotPassword.objects.create(user_id=user.id, otp=otp_value,
                                                        expiration_date=timezone.now()
                                                        + timedelta(minutes=OTP_EXPIRE_TIME))
            context = {OTP_KEY: otp_details.otp,
                       'X': OTP_EXPIRE_TIME,
                       'username': user.name}
            html_content = render_to_string('job/otp_email.html', context)
            Email.objects.create(to_email=email,
                                 from_email=FROM_EMAIL,
                                 subject=SUBJECT_PREFIX
                                 + Messages.ONE_TIME_PASSWORD,
                                 message=html_content)

            msg = EmailMessage(RESET_EMAIL_SUBJECT,
                               html_content, FROM_EMAIL, [user.email])
            msg.content_subtype = "html"
            msg.send()

            otp_details.otp_status_type = OtpStatusType.SUCCESS
            otp_details.save()
            response_data = HulUtility.data_wrapper(status_code=status.HTTP_200_OK,
                                                    message=Messages.OTP_SENT)
        else:
            response_data = HulUtility.data_wrapper(
                status_code=HTTP_USER_ERROR)
            response_data[MESSAGE_KEY] = Messages.NOT_FOUND
        return Response(response_data, status=status.HTTP_200_OK)

# =========================================================================
# Validate OTP API to send OTP on mail using jobs
# =========================================================================


class ValidateOTP(generics.RetrieveAPIView):
    '''
    API for OTP validation
    '''

    def post(self, request):
        '''
        Api to varify valid otp
        '''
        otp_value = request.data.get(OTP_KEY, None)
        email = request.data.get(EMAIL, None)
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            pwd_model = ForgotPassword.objects.filter(
                user_id=user.id, otp=otp_value).first()
            response_data = {}
            if pwd_model:
                message, valid_status = self._validate_otp(
                    pwd_model, otp_value)
                if valid_status:
                    token_value = HulUtility.random_token()
                    response = {}
                    response[TOKEN_KEY] = str(token_value)
                    response_data = HulUtility.data_wrapper(
                        token_value, message=message)
                    pwd_model.token = token_value
                    pwd_model.save()
                else:
                    response_data = HulUtility.data_wrapper()
                    response_data[MESSAGE_KEY] = message
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_INVALID_OTP)
                response_data[MESSAGE_KEY] = Messages.INVALID_OTP
                return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = HulUtility.data_wrapper()
            response_data[MESSAGE_KEY] = Messages.NOT_FOUND
            return Response(response_data, status=status.HTTP_200_OK)

    @classmethod
    def _validate_otp(cls, pwd_model, otp):
        ''' protected method for validate OTP '''
        otp_time = datetime.now(timezone.utc)
        response = Messages.OTP_INVALID
        if pwd_model.expiration_date <= otp_time:
            response = Messages.OTP_INVALID
        elif int(pwd_model.otp_status_type) == OtpStatusType.SUCCESS\
                and int(pwd_model.otp) == int(otp):
            pwd_model.otp_status_type = OtpStatusType.VERIFIED
            pwd_model.save()
            return Messages.OTP_VALIDATED_SUCCESSFULLY, True
        return response, False


# =========================================================================
# Reset password API to set new password
# =========================================================================
class ResetPasswordView(generics.UpdateAPIView):
    '''
    API for Reset password
    '''

    def post(self, request, *args, **kwargs):
        '''
        User Reset Password
        '''
        token = request.data.get(TOKEN_KEY, None)
        new_pwd = request.data.get(PASSWORD, None)
        email = request.data.get(EMAIL, None)
        user = User.objects.filter(email=email, is_active=True).first()
        if user:
            pwd_model = ForgotPassword.objects.filter(
                user_id=user.id, token=token).first()
            response_data = {}
            if not pwd_model or int(pwd_model.otp_status_type) != OtpStatusType.VERIFIED:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_INVALID_TOKEN)
                response_data[MESSAGE_KEY] = Messages.INVALID_TOKEN
            else:
                user_obj = User.objects.filter(
                    email=email, is_active=True).first()
                try:
                    user_obj.set_password(new_pwd)
                    user_obj.save()
                    pwd_model.otp_status_type = OtpStatusType.USED
                    pwd_model.save()
                    lst_acces_token = AccessToken.objects.filter(user=user_obj)
                    HulUtility.expire_token(lst_acces_token)
                    response_data = HulUtility.data_wrapper(
                        message=Messages.PASSWORD_CHANGED_SUCCESSFULLY)
                except KeyError:
                    response_data = HulUtility.data_wrapper(
                        status_code=HTTP_INVALID_TOKEN)
                    response_data[MESSAGE_KEY] = Messages.INVALID_TOKEN
        else:
            response_data = HulUtility.data_wrapper()
            response_data[MESSAGE_KEY] = Messages.NOT_FOUND
        return Response(response_data, status=status.HTTP_200_OK)

# =========================================================================
# Get User Profile Using UserToken
# =========================================================================


class SEProfile(generics.RetrieveAPIView):
    '''
        API for save the data for user sending request
    '''
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        '''
        for handling get request of view profile
        '''
        response_data = {}
        if request.user.id:
            shakti_enterpreneur = ShaktiEntrepreneur.objects.filter(user_id=request.user.pk,
                                                                    is_active=True)
            user_serializer = ShaktiEntrepreneurSerializer(
                shakti_enterpreneur, many=True)
            response = user_serializer.data[0]
            response_data = HulUtility.data_wrapper(
                response, message=SUCCESS_MESSAGE_KEY)
        else:
            response_data = HulUtility.data_wrapper(
                status_code=HTTP_USER_ERROR)
            response_data[MESSAGE_KEY] = Messages.NOT_FOUND
        return Response(response_data, status=status.HTTP_200_OK)

# =========================================================================
# Get User Profile Using UserToken
# =========================================================================


class Profile(generics.RetrieveUpdateAPIView):
    '''
        API for save the data for user sending request
    '''
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        '''
        for handling get request of view profile
        '''
        response_data = {}
        if request.user.id:
            user_serializer = UserSerializer(request.user)
            response = user_serializer.data
            response_data = HulUtility.data_wrapper(
                response, message=SUCCESS_MESSAGE_KEY)
        else:
            response_data = HulUtility.data_wrapper(
                status_code=HTTP_USER_ERROR)
            response_data[MESSAGE_KEY] = Messages.NOT_FOUND
        return Response(response_data, status=status.HTTP_200_OK)

    @classmethod
    def patch(cls, request):
        '''
        Partialy update object
        '''
        user = request.user
        if user:
            response = {}
            response_data = {}
            serializer = UserSerializer(user, request.data, partial=True)
            if serializer.is_valid():
                user = serializer.save()
                user_serializer = UserSerializer(user)
                response = user_serializer.data
                response_data = HulUtility.data_wrapper(
                    response, message=SUCCESS_MESSAGE_KEY)
            else:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = serializer.error_messages
        else:
            response_data = HulUtility.data_wrapper(
                status_code=HTTP_USER_ERROR)
            response_data[MESSAGE_KEY] = Messages.NOT_FOUND
        return Response(response_data, status=status.HTTP_200_OK)


# =========================================================================
# User Change Password Api
# =========================================================================
class ChangePassword(generics.UpdateAPIView):
    '''
    API for Change Password
    '''
    serializer_class = UserSerializer

    def post(self, request):
        '''
        Change Password
        '''
        old_password = self.request.data.get(OLD_PASSWORD, None)
        new_password = self.request.data.get(NEW_PASSWORD, None)
        user = request.user
        if user.id:
            self.check_object_permissions(self.request, user)
            match = user.check_password(old_password)
            response_data = {}
            if match:
                user.set_password(new_password)
                user.save()
                response_data = HulUtility.data_wrapper(
                    message=Messages.PASSWORD_CHANGED_SUCCESSFULLY)
            else:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_INVALID_PASSWORD)
                response_data[MESSAGE_KEY] = Messages.INVALID_PASSWORD
        else:
            response_data = HulUtility.data_wrapper(
                status_code=status.HTTP_401_UNAUTHORIZED)
            response_data[MESSAGE_KEY] = Messages.ACCESS_TOKEN_EXPIRED
        return Response(response_data, status=status.HTTP_200_OK)


# =========================================================================
# List GetShaktiEntrepreneur Api
# =========================================================================
class GetShaktiEntrepreneur(generics.ListAPIView):
    '''
    API for Change Password
    '''
    serializer_class = ShaktiEntrepreneurSerializer

    def get(self, request, page):
        user = request.user
        if user.id:
            shakti_list = ShaktiEntrepreneur.objects.filter(regional_sales__user=user.id,
                                                            is_active=True)

            paginator = Paginator(shakti_list, SHAKTI_ENTERPERNEUR_LIST_SIZE)

            try:
                shakti_list = paginator.page(page)
            except PageNotAnInteger:
                shakti_list = paginator.page(1)
            except EmptyPage:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
                return Response(response_data, status=status.HTTP_200_OK)

            response = {}
            serializer = ShaktiEntrepreneurSerializer(shakti_list, many=True)
            response_data = {}
            response = {}
            if serializer.data:
                response = serializer.data
                response_data = HulUtility.data_wrapper(
                    response, message=SUCCESS_MESSAGE_KEY)
            else:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
        else:
            response_data = HulUtility.data_wrapper(
                status_code=status.HTTP_401_UNAUTHORIZED)
            response_data[MESSAGE_KEY] = Messages.ACCESS_TOKEN_EXPIRED
        return Response(response_data, status=status.HTTP_200_OK)


# =========================================================================
# List AlliancePartner Api
# =========================================================================
class GetAlliancePartner(generics.ListAPIView):
    '''
    API for Change Password
    '''
    serializer_class = AlliancePartnerSerializer

    def get(self, request, page):
        user = request.user
        if user.id:
            sales_promoter = RegionalSalesPromoter.objects.filter(
                user=request.user).select_related('regional_distributor').first()
            shakti_enterpreneur = ShaktiEntrepreneur.objects.filter(
                user=request.user).first()
            if sales_promoter:
                regional_distributor = sales_promoter.regional_distributor.pk
            else:
                regional_distributor = shakti_enterpreneur.regional_sales.regional_distributor_id

            alliance_partners = RegionalDistributor.objects.values('alliance_partner').\
                filter(pk=regional_distributor, is_active=True)
            alliance_partner_ids = [alliance['alliance_partner']
                                    for alliance in alliance_partners]
            alliance_partner_list = AlliancePartner.objects.filter(pk__in=alliance_partner_ids,
                                                                   is_active=True)
            paginator = Paginator(alliance_partner_list,
                                  ALLIANCE_PARTNER_LIST_SIZE)

            try:
                alliance_partner_list = paginator.page(page)
            except PageNotAnInteger:
                alliance_partner_list = paginator.page(1)
            except EmptyPage:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
                return Response(response_data, status=status.HTTP_200_OK)

            response = {}
            serializer = AlliancePartnerSerializer(
                alliance_partner_list, many=True)
            response_data = {}
            response = {}
            if serializer.data:
                response = serializer.data
                response_data = HulUtility.data_wrapper(
                    response, message=SUCCESS_MESSAGE_KEY)
            else:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
        else:
            response_data = HulUtility.data_wrapper(
                status_code=status.HTTP_401_UNAUTHORIZED)
            response_data[MESSAGE_KEY] = Messages.ACCESS_TOKEN_EXPIRED
        return Response(response_data, status=status.HTTP_200_OK)
