# Copyright (C) 2010, 2011  SPARTA, Inc. dba Cobham Analytic Solutions
# Copyright (C) 2012  SPARTA, Inc. a Parsons Company
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND SPARTA DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS.  IN NO EVENT SHALL SPARTA BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

__version__ = '$Id$'


from django.contrib.auth.models import User
from django import forms
from rpki.resource_set import (resource_range_as, resource_range_ipv4,
                               resource_range_ipv6)
from rpki.gui.app import models
from rpki.exceptions import BadIPResource
from rpki.gui.app.glue import str_to_resource_range


class AddConfForm(forms.Form):
    handle = forms.CharField(required=True,
            help_text='your handle for your rpki instance')
    run_rpkid = forms.BooleanField(required=False, initial=True,
            label='Run rpkid?',
            help_text='do you want to run your own instance of rpkid?')
    rpkid_server_host = forms.CharField(initial='rpkid.example.org',
            label='rpkid hostname',
            help_text='publicly visible hostname for your rpkid instance')
    rpkid_server_port = forms.IntegerField(initial=4404,
            label='rpkid port')
    run_pubd = forms.BooleanField(required=False, initial=False,
            label='Run pubd?',
            help_text='do you want to run your own instance of pubd?')
    pubd_server_host = forms.CharField(initial='pubd.example.org',
            label='pubd hostname',
            help_text='publicly visible hostname for your pubd instance')
    pubd_server_port = forms.IntegerField(initial=4402, label='pubd port')
    pubd_contact_info = forms.CharField(initial='repo-man@rpki.example.org',
            label='Pubd contact',
            help_text='email address for the operator of your pubd instance')


class GhostbusterRequestForm(forms.ModelForm):
    """
    Generate a ModelForm with the subset of parents for the current
    resource handle.
    """
    # override default form field
    parent = forms.ModelChoiceField(queryset=None, required=False,
            help_text='Specify specific parent, or none for all parents')

    # override full_name.  it is required in the db schema, but we allow the
    # user to skip it and default from family+given name
    full_name = forms.CharField(max_length=40, required=False,
            help_text='automatically generated from family and given names if left blank')

    def __init__(self, issuer, *args, **kwargs):
        super(GhostbusterRequestForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = models.Parent.objects.filter(issuer=issuer)

    class Meta:
        model = models.GhostbusterRequest
        exclude = ('issuer', 'vcard')

    def clean(self):
        family_name = self.cleaned_data.get('family_name')
        given_name = self.cleaned_data.get('given_name')
        if not all([family_name, given_name]):
            raise forms.ValidationError, 'Family and Given names must be specified'

        email = self.cleaned_data.get('email_address')
        postal = self.cleaned_data.get('postal_address')
        telephone = self.cleaned_data.get('telephone')
        if not any([email, postal, telephone]):
            raise forms.ValidationError, 'One of telephone, email or postal address must be specified'

        # if the full name is not specified, default to given+family
        fn = self.cleaned_data.get('full_name')
        if not fn:
            self.cleaned_data['full_name'] = '%s %s' % (given_name, family_name)

        return self.cleaned_data


class ImportForm(forms.Form):
    """Form used for uploading parent/child identity xml files."""
    handle = forms.CharField(required=False,
                             widget=forms.TextInput(attrs={'class': 'xlarge'}),
                             help_text='Optional.  Your name for this entity, or blank to accept name in XML')
    xml = forms.FileField(label='XML file',
                          widget=forms.FileInput(attrs={'class': 'input-file'}))


class ImportRepositoryForm(forms.Form):
    handle = forms.CharField(max_length=30, required=False,
                             label='Parent Handle',
                             help_text='Optional.  Must be specified if you use a different name for this parent')
    xml = forms.FileField(label='XML file',
                          widget=forms.FileInput(attrs={'class': 'input-file'}))


class ImportClientForm(forms.Form):
    """Form used for importing publication client requests."""
    xml = forms.FileField(label='XML file',
                          widget=forms.FileInput(attrs={'class': 'input-file'}))


class UserCreateForm(forms.Form):
    handle = forms.CharField(max_length=30, help_text='handle for new child')
    email = forms.CharField(max_length=30,
                            help_text='email address for new user')
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput,
                                label='Confirm Password')
    parent = forms.ModelChoiceField(required=False,
                                    queryset=models.Conf.objects.all(),
                                    help_text='optionally make a child of')

    def clean_handle(self):
        handle = self.cleaned_data.get('handle')
        if (handle and models.Conf.objects.filter(handle=handle).exists() or
            User.objects.filter(username=handle).exists()):
            raise forms.ValidationError('user already exists')
        return handle

    def clean(self):
        p1 = self.cleaned_data.get('password')
        p2 = self.cleaned_data.get('password2')
        if p1 != p2:
            raise forms.ValidationError('passwords do not match')
        handle = self.cleaned_data.get('handle')
        parent = self.cleaned_data.get('parent')
        if handle and parent and parent.children.filter(handle=handle).exists():
            raise forms.ValidationError('parent already has a child by that name')
        return self.cleaned_data


class ROARequest(forms.Form):
    """Form for entering a ROA request.

    Handles both IPv4 and IPv6."""

    asn = forms.IntegerField(label='AS')
    prefix = forms.CharField(max_length=50)
    max_prefixlen = forms.CharField(required=False,
            label='Max Prefix Length')
    confirmed = forms.BooleanField(widget=forms.HiddenInput, required=False)

    def _as_resource_range(self):
        prefix = self.cleaned_data.get('prefix')
        return str_to_resource_range(prefix)

    def clean_asn(self):
        value = self.cleaned_data.get('asn')
        if value < 0:
            raise forms.ValidationError('AS must be a positive value or 0')
        return value

    def clean_prefix(self):
        try:
            r = self._as_resource_range()
        except:
            raise forms.ValidationError('invalid IP address')
        return str(r)

    def clean_max_prefixlen(self):
        v = self.cleaned_data.get('max_prefixlen')
        if v:
            if v[0] == '/':
                v = v[1:]  # allow user to specify /24
            if int(v) < 0:
                raise forms.ValidationError('max prefix length must be positive or 0')
        return v

    def clean(self):
        if 'prefix' in self.cleaned_data:
            r = self._as_resource_range()
            max_prefixlen = self.cleaned_data.get('max_prefixlen')
            max_prefixlen = int(max_prefixlen) if max_prefixlen else r.prefixlen()
            if max_prefixlen < r.prefixlen():
                raise forms.ValidationError('max prefix length must be greater than or equal to the prefix length')
            if max_prefixlen > r.datum_type.bits:
                raise forms.ValidationError, \
                        'max prefix length (%d) is out of range for IP version (%d)' % (max_prefixlen, r.datum_type.bits)
            self.cleaned_data['max_prefixlen'] = str(max_prefixlen)

        return self.cleaned_data


class ROARequestConfirm(forms.Form):
    asn = forms.IntegerField(widget=forms.HiddenInput)
    prefix = forms.CharField(widget=forms.HiddenInput)
    max_prefixlen = forms.IntegerField(widget=forms.HiddenInput)

    def clean_asn(self):
        value = self.cleaned_data.get('asn')
        if value < 0:
            raise forms.ValidationError('AS must be a positive value or 0')
        return value

    def clean_prefix(self):
        try:
            r = str_to_resource_range(self.cleaned_data.get('prefix'))
        except BadIPResource:
            raise forms.ValidationError('invalid prefix')
        return str(r)

    def clean(self):
        try:
            r =str_to_resource_range(self.cleaned_data.get('prefix'))
            if r.prefixlen() > self.cleaned_data.get('max_prefixlen'):
                raise forms.ValidationError('max length is smaller than mask')
        except BadIPResource:
            pass
        return self.cleaned_data


def AddASNForm(qs):
    """
    Generate a form class which only allows specification of ASNs contained
    within the specified queryset.  `qs` should be a QuerySet of
    irdb.models.ChildASN.

    """

    class _wrapped(forms.Form):
        asns = forms.CharField(label='ASNs', help_text='single ASN or range')

        def clean_asns(self):
            try:
                r = resource_range_as.parse_str(self.cleaned_data.get('asns'))
            except:
                raise forms.ValidationError('invalid AS or range')
            if not qs.filter(min__lte=r.min, max__gte=r.max).exists():
                raise forms.ValidationError('AS or range is not delegated to you')
            return str(r)

    return _wrapped


def AddNetForm(qsv4, qsv6):
    """
    Generate a form class which only allows specification of prefixes contained
    within the specified queryset.  `qs` should be a QuerySet of
    irdb.models.ChildNet.

    """

    class _wrapped(forms.Form):
        address_range = forms.CharField(help_text='CIDR or range')

        def clean_address_range(self):
            address_range = self.cleaned_data.get('address_range')
            try:
                r = resource_range_ipv4.parse_str(address_range)
                if not qsv4.filter(prefix_min__lte=r.min, prefix_max__gte=r.max).exists():
                    raise forms.ValidationError('IP address range is not delegated to you')
            except BadIPResource:
                try:
                    r = resource_range_ipv6.parse_str(address_range)
                    if not qsv6.filter(prefix_min__lte=r.min, prefix_max__gte=r.max).exists():
                        raise forms.ValidationError('IP address range is not delegated to you')
                except BadIPResource:
                    raise forms.ValidationError('invalid IP address range')
            return str(r)

    return _wrapped


def ChildForm(instance):
    """
    Form for editing a Child model.

    This is roughly based on the equivalent ModelForm, but uses Form as a base
    class so that selection boxes for the AS and Prefixes can be edited in a
    single form.

    """

    class _wrapped(forms.Form):
        valid_until = forms.DateTimeField(initial=instance.valid_until)
        as_ranges = forms.ModelMultipleChoiceField(queryset=models.ChildASN.objects.filter(child=instance),
                                                   required=False,
                                                   label='AS Ranges',
                                                   help_text='deselect to remove delegation')
        address_ranges = forms.ModelMultipleChoiceField(queryset=models.ChildNet.objects.filter(child=instance),
                                                        required=False,
                                                        help_text='deselect to remove delegation')

    return _wrapped


class UserDeleteForm(forms.Form):
    """Stub form for deleting users."""
    pass
