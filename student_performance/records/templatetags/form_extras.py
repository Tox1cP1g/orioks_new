from django import template

register = template.Library()


@register.filter
def add_class(field, class_name):
    """Добавляет CSS класс к полю формы."""
    return field.as_widget(attrs={'class': class_name})
