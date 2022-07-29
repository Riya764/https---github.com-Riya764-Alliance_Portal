''' app/forms.py '''
import re
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from django.db.models import Q
from s3direct.widgets import S3DirectWidget
from app.models import (UserAddress, DistributorNorm, RegionalDistributor, AlliancePartner ,RegionalDistributor, RegionalSalesPromoter, ShaktiEntrepreneur)
from localization.models import State
from product.models import Product


class UserImportForm(forms.Form):
    '''Import Shakti form'''
    import_file = forms.FileField()


class UserBaseForm(forms.ModelForm):
    '''User form base class'''
    name = forms.CharField(max_length=50)
    email = forms.EmailField(max_length=80)
    username = forms.CharField(max_length=50)
    contact_number = forms.CharField(max_length=20, help_text=mark_safe(
        'Please enter 10 digit number e.g. 9876543210'))
    address_line1 = forms.CharField(max_length=50)
    address_line2 = forms.CharField(max_length=50)
    address_line3 = forms.CharField(max_length=50, required=False)
    state = forms.ModelChoiceField(
        queryset=State.objects.filter(is_active=True))
    city = forms.CharField(max_length=50)
    post_code = forms.CharField(max_length=50)
    image = forms.URLField(widget=S3DirectWidget(dest='user_images'),
                           required=False,
                           help_text=mark_safe('Recommended size for image 300x300'))


class AddUserForm(UserBaseForm):
    '''User add form with password field'''
    password = forms.CharField(
        max_length=55, min_length=6, widget=forms.PasswordInput)
    confirm_password = forms.CharField(
        max_length=55, min_length=6, widget=forms.PasswordInput)

    def clean_email(self):
        '''cleane email field'''
        user = get_user_model().objects.filter(
            email__iexact=self.cleaned_data['email']).first()
        if user:
            raise forms.ValidationError("User with %s email already exists"
                                        % (self.cleaned_data['email']))
        return self.cleaned_data['email']

    def clean_username(self):
        '''Clean username field'''
        regex = r'\s'
        if re.search(regex, self.cleaned_data['username']):
            raise forms.ValidationError("Space not allowed in username")
        user = get_user_model().objects.filter(
            username__iexact=self.cleaned_data['username']).first()
        if user:
            raise forms.ValidationError("User with %s username already\
                                         exists" % (self.cleaned_data['username']))
        return self.cleaned_data['username']

    def clean_password(self):
        '''Clean Password field'''
        password = self.data.get('password', None)
        confirm_password = self.data.get('confirm_password', None)

        if password != confirm_password:
            raise forms.ValidationError(
                "Password and Confirm Password does not match.")
        return password

    def save(self, *args, **kwargs):
        address_line1 = self.cleaned_data.pop('address_line1', None)
        address_line2 = self.cleaned_data.pop('address_line2', None)
        address_line3 = self.cleaned_data.pop('address_line3', None)
        city = self.cleaned_data.pop('city', None)
        state = self.cleaned_data.pop('state', None)
        post_code = self.cleaned_data.pop('post_code', None)

        address = UserAddress.objects.create(address_line1=address_line1,
                                             address_line2=address_line2,
                                             address_line3=address_line3,
                                             city=city, state=state, post_code=post_code)
        username = self.cleaned_data.pop('username', None)
        password = self.cleaned_data.pop('password', None)
        email = self.cleaned_data.pop('email', None)
        name = self.cleaned_data.pop('name', None)
        image = self.cleaned_data.pop('image', None)
        contact_number = self.cleaned_data.pop('contact_number', None)
        user = get_user_model().objects.create_user(email=email, password=password,
                                                    username=username, name=name,
                                                    contact_number=contact_number,
                                                    image=image)
        instance = super(AddUserForm, self).save(*args, **kwargs)
        instance.user = user
        instance.address = address
        instance.save()
        return instance

    class Meta(object):
        '''Exclude user and address field to show in form'''
        exclude = ('user', 'address',)


class UserChangeForm(UserBaseForm):
    '''Class for user change form'''
    code = forms.CharField(max_length=55)
    username = forms.CharField(max_length=50)

    class Meta(object):
        '''Exclude user and address field to show in form'''
        exclude = ('user', 'address',)

    def __init__(self, *args, **kwargs):
        kwargs['initial'] = kwargs.get('initial', {})
        kwargs['initial'].update({'name': kwargs['instance'].user.name,
                                  'image': kwargs['instance'].user.image,
                                  'username': kwargs['instance'].user.username,
                                  'email': kwargs['instance'].user.email,
                                  'contact_number': kwargs['instance'].user.contact_number})
        kwargs['initial'].update({'address_line1': kwargs['instance'].address.address_line1,
                                  'address_line2': kwargs['instance'].address.address_line2,
                                  'address_line3': kwargs['instance'].address.address_line3,
                                  'city': kwargs['instance'].address.city,
                                  'state': kwargs['instance'].address.state,
                                  'post_code': kwargs['instance'].address.post_code,
                                  'code': kwargs['instance'].code})
        self.user = kwargs['instance'].user
        self.address = kwargs['instance'].address

        super(UserChangeForm, self).__init__(*args, **kwargs)

    def _update_user(self, name, username, email, contact_number, image):
        self.user.email = email
        self.user.username = username
        self.user.name = name
        self.user.image = image
        self.user.contact_number = contact_number
        self.user.save()
        return self.user

    def _update_address(self, address_line1, address_line2, address_line3, city, state, post_code):
        self.address.address_line1 = address_line1
        self.address.address_line2 = address_line2
        self.address.address_line3 = address_line3
        self.address.city = city
        self.address.state = state
        self.address.post_code = post_code

        self.address.save()
        return self.address

    def clean_email(self):
        ''' Clean Email address '''
        user = get_user_model().objects.filter(Q(email__iexact=self.cleaned_data['email'])
                                               & ~Q(pk=self.instance.user.pk)).first()
        if user:
            raise forms.ValidationError("User with %s email already exists"
                                        % (self.cleaned_data['email']))
        return self.cleaned_data['email']

    def save(self, *args, **kwargs):
        username = self.cleaned_data.pop('username', None)
        name = self.cleaned_data.pop('name', None)
        image = self.cleaned_data.pop('image', None)
        email = self.cleaned_data.pop('email', None)
        contact_number = self.cleaned_data.pop('contact_number', None)

        self._update_user(name, username, email, contact_number, image)

        address_line1 = self.cleaned_data.pop('address_line1', None)
        address_line2 = self.cleaned_data.pop('address_line2', None)
        address_line3 = self.cleaned_data.pop('address_line3', None)
        city = self.cleaned_data.pop('city', None)
        state = self.cleaned_data.pop('state', None)
        post_code = self.cleaned_data.pop('post_code', None)

        self._update_address(address_line1, address_line2,
                             address_line3, city, state, post_code)

        return super(UserChangeForm, self).save(*args, **kwargs)


class RSPUserChangeForm(UserBaseForm):
    '''Custom RSP user Change form'''
    username = forms.CharField(max_length=50)
    regional_distributor = forms.ModelChoiceField(queryset=RegionalDistributor.active_rs.all())

    class Meta(object):
        exclude = ('user', 'address',)

    def __init__(self, *args, **kwargs):
        kwargs['initial'] = kwargs.get('initial', {})
        kwargs['initial'].update({'name': kwargs['instance'].user.name,
                                  'image': kwargs['instance'].user.image,
                                  'username': kwargs['instance'].user.username,
                                  'email': kwargs['instance'].user.email,
                                  'contact_number': kwargs['instance'].user.contact_number})
        kwargs['initial'].update({'address_line1': kwargs['instance'].address.address_line1,
                                  'address_line2': kwargs['instance'].address.address_line2,
                                  'address_line3': kwargs['instance'].address.address_line3,
                                  'city': kwargs['instance'].address.city,
                                  'state': kwargs['instance'].address.state,
                                  'post_code': kwargs['instance'].address.post_code})
        self.user = kwargs['instance'].user
        self.address = kwargs['instance'].address
        super(RSPUserChangeForm, self).__init__(*args, **kwargs)


    def _update_user(self, name, username, email, contact_number, image):
        self.user.email = email
        self.user.username = username
        self.user.name = name
        self.user.image = image
        self.user.contact_number = contact_number

        self.user.save()
        return self.user

    def _update_address(self, address_line1, address_line2, address_line3, city, state, post_code):
        self.address.address_line1 = address_line1
        self.address.address_line2 = address_line2
        self.address.address_line3 = address_line3
        self.address.city = city
        self.address.state = state
        self.address.post_code = post_code

        self.address.save()
        return self.address

    def clean_email(self):
        ''' Clean Mail '''
        user = get_user_model().objects.filter(Q(email__iexact=self.cleaned_data['email'])
                                               & ~Q(pk=self.instance.user.pk)).first()
        if user:
            raise forms.ValidationError("User with %s email already exists"
                                        % (self.cleaned_data['email']))
        return self.cleaned_data['email']

    def clean_username(self):
        ''' Clean Username '''
        user = get_user_model().objects.filter(Q(username=self.cleaned_data['username'])
                                               & ~Q(pk=self.instance.user.pk)).first()
        if user:
            raise forms.ValidationError("User with %s username already exists"
                                        % (self.cleaned_data['username']))
        return self.cleaned_data['username']

    def save(self, *args, **kwargs):
        username = self.cleaned_data.pop('username', None)
        name = self.cleaned_data.pop('name', None)
        image = self.cleaned_data.pop('image', None)
        email = self.cleaned_data.pop('email', None)
        contact_number = self.cleaned_data.pop('contact_number', None)
        self._update_user(name, username, email, contact_number, image)

        address_line1 = self.cleaned_data.pop('address_line1', None)
        address_line2 = self.cleaned_data.pop('address_line2', None)
        address_line3 = self.cleaned_data.pop('address_line3', None)
        city = self.cleaned_data.pop('city', None)
        state = self.cleaned_data.pop('state', None)
        post_code = self.cleaned_data.pop('post_code', None)

        self._update_address(address_line1, address_line2, address_line3,
                             city, state, post_code)

        return super(RSPUserChangeForm, self).save(*args, **kwargs)


class DistributorNormForm(forms.ModelForm):

    class Meta:
        model = DistributorNorm
        fields = ('distributor', 'product', 'norm', )

    def __init__(self, *args, **kwargs):
        super(DistributorNormForm, self).__init__(*args, **kwargs)
        norm_instance = self.instance
        if not norm_instance.id:
            self.fields['product'].queryset = Product.active_products.all()
            self.fields['distributor'].queryset = RegionalDistributor.active_rs.all()


class AddRspUserForm(AddUserForm):
    regional_distributor = forms.ModelChoiceField(queryset=RegionalDistributor.active_rs.all())


class AddRegionalDistributorForm(AddUserForm):
    alliance_partner = forms.ModelMultipleChoiceField(
        queryset=AlliancePartner.active_ap.all(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name='Alliance Partner',
            is_stacked=False
        )
    )

class AddShaktiform(AddUserForm):
    regional_sales = forms.ModelChoiceField(queryset=RegionalSalesPromoter.active_rsp.all())


class ChangeRegionalDistributorForm(UserChangeForm):
    alliance_partner = forms.ModelMultipleChoiceField(
        queryset=AlliancePartner.active_ap.all(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name='Alliance Partner',
            is_stacked=False
        )
    )

class ChangeShaktiform(UserChangeForm):
    regional_sales = forms.ModelChoiceField(queryset=RegionalSalesPromoter.active_rsp.all())