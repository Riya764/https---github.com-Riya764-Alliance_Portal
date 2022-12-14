''' select widget with disabled options '''
from django.forms.widgets import Select
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape


class SelectWithDisabled(Select):
    """
    Subclass of Django's select widget that allows disabling options.
    To disable an option, pass a dict instead of a string for its label,
    of the form: {'label': 'option label', 'disabled': True}
    """

    def render_option(self, selected_choices, option_value, option_label):
        ''' django's subclass of select widget '''
        option_value = force_unicode(option_value)
        if option_value in selected_choices:
            selected_html = u' selected="selected"'
        else:
            selected_html = ''
        disabled_html = ''
        if isinstance(option_label, dict):
            if dict.get(option_label, 'disabled'):
                disabled_html = u' disabled="disabled"'
            option_label = option_label['label']

        return u'<option value="%s"%s%s>%s</option>' % (
            escape(option_value), selected_html, disabled_html,
            conditional_escape(force_unicode(option_label)))


class SelectWithDisabled_new(Select):
    """
    Subclass of Django's select widget that allows disabling options.
    To disable an option, pass a dict instead of a string for its label,
    of the form: {'label': 'option label', 'disabled': True}
    """

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        disabled = False
        if isinstance(label, dict):
            label, disabled = label['label'], label['disabled']
        option_dict = super(SelectWithDisabled, self).create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if disabled:
            option_dict['attrs']['disabled'] = 'disabled'
        return option_dict
