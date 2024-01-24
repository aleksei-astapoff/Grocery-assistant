import webcolors
from django import forms
from .models import Tag
from .widgets import ColorPickerWidget


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = '__all__'
        widgets = {
            'color': ColorPickerWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        color = cleaned_data.get('color')

        if color and not color.startswith('#'):
            try:

                color = webcolors.name_to_hex(color)
            except ValueError:
                self.add_error(
                    f'{color}, '
                    f'Указанное значение цвета неверно или не поддерживается.'
                )
        cleaned_data['color'] = color
        return cleaned_data
