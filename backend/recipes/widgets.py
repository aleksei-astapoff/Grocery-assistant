import webcolors
from django import forms
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

NAMED_COLORS = list(webcolors.CSS3_HEX_TO_NAMES.items())
SELECTED_COLORS = (hex_value for name, hex_value
                   in NAMED_COLORS if len(hex_value) <= 7)


class ColorPickerWidget(forms.Widget):
    template_name = 'color_picker.html'

    def value_from_datadict(self, data, files, name):
        hex_color = data.get(name)
        if hex_color:
            hex_color = hex_color.lstrip('#')
        return hex_color

    def render(self, name, value, attrs=None, renderer=None):
        if value and not value.startswith('#'):
            value = f'#{value}'
        context = {
            'color_choices': SELECTED_COLORS,
            'input_name': name,
            'value': value,
        }
        return mark_safe(render_to_string('color_picker.html', context))
