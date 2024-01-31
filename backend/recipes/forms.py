import webcolors
from django import forms
from .models import Tag
from .widgets import ColorPickerWidget


class TagForm(forms.ModelForm):
    """Форма для отображения  виджета в Админпанели Тэгов."""
    class Meta:
        model = Tag
        fields = '__all__'
        widgets = {
            'color': ColorPickerWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        color = cleaned_data.get("color")

        if not color:
            self.add_error('color', 'Выберите цвет')
        else:
            try:
                cleaned_data["color"] = webcolors.name_to_hex(color)
            except ValueError:
                self.add_error('color', 'Обязательное поле.')

        return cleaned_data
