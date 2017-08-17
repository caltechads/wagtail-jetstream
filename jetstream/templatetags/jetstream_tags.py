import re

from django import template
from django.utils.safestring import mark_safe
from wagtail.wagtailembeds.exceptions import EmbedException
from wagtail.wagtailembeds import embeds

register = template.Library()

@register.simple_tag(name='arbitrary_video')
def arbitrary_video(video, width, height):
    """
    Renders an embedded video with the given width and height.
    """
    try:
        embed = embeds.get_embed(video.url, width)
        html = embed.html
        # Replace the calculated height value with what the user specified.
        html = re.sub(r'height="(\d+)"', 'height="{}"'.format(height), html)
        # Add the provider name as a data attr, so that the javascript can determine how to interact with this iframe.
        html = re.sub(r'<iframe', '<iframe data-provider="{}"'.format(embed.provider_name), html)

        # Remove the video player chrome.
        if embed.provider_name == 'YouTube':
            html = re.sub(r'feature=oembed', 'feature=oembed&showinfo=0', html)
        elif embed.provider_name == 'Vimeo':
            # We can't get rid of all of the Vimeo chrome, but this does as much as we can.
            html = re.sub(
                r'player\.vimeo\.com/video/(\d+)',
                r'player.vimeo.com/video/\1?title=0&byline=0&portrait=0',
                html
            )
        return mark_safe(html)
    except EmbedException:
        # Silently ignore failed embeds, rather than letting them crash the page.
        return ''


@register.tag(name='arbitrary_image')
def arbitrary_image(parser, token):
    """
    Usage: {% arbitrary_image self.image __MODE__ __WIDTH__ __HEIGHT__ [ custom-attr="value" ... ] %}
           {% arbitrary_image self.image __MODE__ __WIDTH__ __HEIGHT__ as img %}
    """

    return parse_image_tag('arbitrary_image', parser, token, ArbitraryImageNode)

class ResponsiveImageNode(ImageNode):

    def render(self, context):
        try:
            image = self.image_expr.resolve(context)
            width = int(self.width_expr.resolve(context))
            height = int(self.height_expr.resolve(context))
            mode = self.mode_expr.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        if not image:
            return ''

        # Build a filter spec based on the specified mode, height, and width for the base rendition.
        base_spec = "{}-{}x{}-c100".format(mode, width, height)
        base_rendition = get_rendition_or_not_found(image, Filter(spec=base_spec))
        # Build another filter spec that generates a square rendition with length and width equal to the shortest side.
        square_spec = "{}-{}x{}-c100".format(mode, min(width, height), min(width, height))
        square_rendition = get_rendition_or_not_found(image, Filter(spec=square_spec))
        # Build the fallback <img> tag for browsers that don't support <picture>.
        custom_attrs = {attr_name: expression.resolve(context) for attr_name, expression in self.attrs.items()}
        img_tag = base_rendition.img_tag(custom_attrs)

        # For now, we render just two sources:
        # - the full-size rendition, which we let the browser resise for us on < 1000px devices
        # - a square rendition which we display on portrait oriented phones only.
        return """
            <picture>
              <source srcset="{square.url}" media="(max-width: 499px)">
              <source srcset="{full.url}" media="(min-width: 500px)">
              {img_tag}
            </picture>
        """.format(img_tag=img_tag, full=base_rendition, square=square_rendition)

class ImageNode(template.Node):

    def __init__(self, image_expr, mode_expr, width_expr, height_expr, output_var_name=None, attrs=None):
        self.image_expr = image_expr
        self.mode_expr = mode_expr
        self.width_expr = width_expr
        self.height_expr = height_expr
        self.output_var_name = output_var_name
        self.attrs = attrs or {}

    def render(self, context):
        raise NotImplementedError


class ArbitraryImageNode(ImageNode):

    def render(self, context):
        try:
            image = self.image_expr.resolve(context)
            width = self.width_expr.resolve(context)
            height = self.height_expr.resolve(context)
            mode = self.mode_expr.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        if not image:
            return ''

        # Build a filter spec based on the specified mode, height, and width.
        spec = "{}-{}x{}-c100".format(mode, int(width), int(height))
        rendition = get_rendition_or_not_found(image, Filter(spec=spec))

        if self.output_var_name:
            # Save the rendition into the context, instead of outputting a tag.
            context[self.output_var_name] = rendition
            return ''
        else:
            # Resolve custom attrs to their value in this context, then print them within this rendition's <img> tag.
            custom_attrs = {attr_name: expression.resolve(context) for attr_name, expression in self.attrs.items()}
            return rendition.img_tag(custom_attrs)


@register.simple_tag()
def object_identifier(obj):
    return id(obj)



@register.simple_tag()
def subtract_from_twelve(*numbers):
    """
    Math tag for calculating the width in Bootstrap's column delineations because we can't do arithmetic
    in Django templates.
    """
    return 12 - sum(int(x) for x in numbers)


@register.simple_tag()
def width_from_arbitrary_parent(parent_px, units):
    """
    Math tag for calculating the pixel width of certain column blocks because we can't do arithmetic
    within Django templates.
    """
    return int(parent_px) / 12 * int(units)

@register.simple_tag(name='link_exists')
def link_exists(block):
    """
    Accessory tag to our LinkBlock sub component that emulates a basic if-check because simply
    checking for the existence of {{ self.link }} will always return true because the link
    component always exists, even if both fields are emtpy.
    """
    return block['page'] or block['url']
