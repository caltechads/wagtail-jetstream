from django.utils.html import format_html
from django.templatetags.static import static
from sass_processor.processor import sass_processor

from wagtail import hooks


@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', sass_processor('jetstream/css/admin.scss'))
