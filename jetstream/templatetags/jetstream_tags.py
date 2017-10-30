from __future__ import division
import re
import uuid

from django import template
from django.utils.safestring import mark_safe
from wagtail.wagtailembeds.exceptions import EmbedException
from wagtail.wagtailcore.models import Page
from wagtail.wagtailembeds import embeds
from wagtail.wagtailimages.models import Filter
from wagtail.wagtailimages.shortcuts import get_rendition_or_not_found

register = template.Library()

PHONE_WIDTH = 768
TABLET_WIDTH = 992
DESKTOP_WIDTH = 1200
# We order these large to small to get sizing rules to order correctly.
VIEWPORT_WIDTHS = [DESKTOP_WIDTH, TABLET_WIDTH, PHONE_WIDTH]


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
           {% arbitrary_image self.image __MODE__ __DIMENSION__ as img %}

    Currently supported MODEs are 'fill', 'max', 'min', 'width', and 'height'.
    The 'width' and 'height' modes take only one dimension argument.
    """
    return parse_image_tag('arbitrary_image', parser, token, ArbitraryImageNode)


@register.tag(name='responsive_image')
def responsive_image(parser, token):
    """
    Usage: {% responsive_image self.image __MODE__ __WIDTH__ __HEIGHT__ [ custom-attr="value" ... ] %}
           {% responsive_image self.image __MODE__ __DIMENSION__ [ custom-attr="value" ... ] %}

    This tag works just like arbitrary_image, but generates a <picture> tag with a few responsive <source>s, instead of
    an <img> tag. Because more than one rendition is generated, using the "as var_name" functionality would be
    ambiguous, so {% responsive_image %} doesn't support it.
    """
    return parse_image_tag('responsive_image', parser, token, ResponsiveImageNode)


class ImageNode(template.Node):

    def __init__(self, image_expr, mode_expr, width_expr=None, height_expr=None, output_var_name=None, attrs=None):
        self.image_expr = image_expr
        self.mode_expr = mode_expr
        self.width_expr = width_expr
        self.height_expr = height_expr
        self.output_var_name = output_var_name
        self.attrs = attrs or {}

    def render(self, context):
        raise NotImplementedError


class ResponsiveImageNode(ImageNode):

    def render(self, context):
        try:
            image = self.image_expr.resolve(context)
            mode = self.mode_expr.resolve(context)
            width = int(self.width_expr.resolve(context)) if self.width_expr else 1
            height = int(self.height_expr.resolve(context)) if self.height_expr else 1
        except template.VariableDoesNotExist:
            return ''

        if not image:
            return ''

        # Build a filter spec based on the specified mode, height, and width for the base rendition.
        if mode == 'width':
            base_spec = "width-{}".format(width)
        elif mode == 'height':
            base_spec = "height-{}".format(height)
        else:
            base_spec = "{}-{}x{}-c100".format(mode, width, height)
        base_rendition = get_rendition_or_not_found(image, Filter(spec=base_spec))

        # Build the fallback <img> tag for browsers that don't support <picture>.
        custom_attrs = {attr_name: expression.resolve(context) for attr_name, expression in self.attrs.items()}
        img_tag = base_rendition.img_tag(custom_attrs)

        # If the image is wider than a phone, add an additional, smaller rendition with the same aspect ratio.
        small_width = 425
        # Two notes here:
        # 1) We used 'from __future__ import division' to make this use floating point division.
        # 2) Filter specs don't accept floats, so we need to cast back to int at the end.
        small_height = int(height * (small_width / width))
        small_spec = "{}-{}x{}-c100".format(mode, small_width, small_height)
        small_rendition = get_rendition_or_not_found(image, Filter(spec=small_spec))

        return """
            <picture>
              <source srcset="{small.url}" media="(max-width: 499px)">
              <source srcset="{full.url}" media="(min-width: 500px)">
              {img_tag}
            </picture>
        """.format(img_tag=img_tag, full=base_rendition, small=small_rendition)


class ArbitraryImageNode(ImageNode):

    def render(self, context):
        try:
            image = self.image_expr.resolve(context)
            mode = self.mode_expr.resolve(context)
            width = int(self.width_expr.resolve(context)) if self.width_expr else 0
            height = int(self.height_expr.resolve(context)) if self.height_expr else 0
        except template.VariableDoesNotExist:
            return ''

        if not image:
            return ''

        # Build a filter spec based on the specified mode, height, and width for the base rendition.
        if mode == 'width':
            spec = "width-{}".format(width)
        elif mode == 'height':
            spec = "height-{}".format(height)
        else:
            spec = "{}-{}x{}-c100".format(mode, width, height)
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
def subtract_from_twelve(*numbers):
    """
    Math tag for calculating the width in Bootstrap's column delineations because we can't do arithmetic
    in Django templates.
    """
    return 12 - sum(int(x) for x in numbers)


@register.simple_tag()
def width_from_arbitrary_parent(parent_px, units, gutter_width):
    """
    Math tag for calculating the pixel width of certain column blocks because we can't do arithmetic
    within Django templates.
    """
    return int((float(parent_px) / 12.0 * float(units)) - float(gutter_width)/2.0)


@register.simple_tag(name='link_url')
def link_url(block):
    """
    Accessory tag to our LinkBlock sub component that returns the linked page if it exists, or the linked
    URL. If neither are specified, returns None.
    """
    if block.get('page'):
        return block['page'].full_url
    elif block.get('url'):
        return block['url']
    else:
        return None


@register.simple_tag()
def page_descendants(page, only_published=True):
    queryset = Page.objects.child_of(page)
    if only_published:
        queryset = queryset.live()
    return queryset


@register.simple_tag()
def page_siblings(page, only_published=True):
    # Results don't include itself, so need to add a non-hyperlink dummy listing
    queryset = page.get_siblings(inclusive=True)
    if only_published:
        queryset = queryset.live()
    return queryset


@register.simple_tag(takes_context=True)
def get_gallery_image_width(context):
    parent_width = context.get('parent_width', None)
    if parent_width is None:
        parent_width = 1000

    number_of_gutters = context['self']['columns'] - 1
    available_pixels = parent_width - (12 * number_of_gutters)
    return available_pixels / context['self']['columns']


@register.simple_tag()
def generate_unique_id():
    """
    Used by the carousel block templates to generate unique IDs when they can't get one from the block itself.
    """
    unique_id = uuid.uuid4()
    return unique_id


# ---------------
# UTIL FUNCTIONS
# ---------------
def parse_image_tag(tag_name, parser, token, node_class):
    """
    Send this function the name of the tag it's parsing for, the arguments to the tag function, and the class of
    ImageNode that you want to be constructed from the parsed data.
    """
    bits = token.split_contents()[1:]
    image_expr = parser.compile_filter(bits[0])
    mode_expr = parser.compile_filter(bits[1])

    # The mode comes in as a string like "'width'", so we need to strip the surrounding quotes.
    mode_string = bits[1].strip("\"\'")
    if mode_string == 'width':
        # The width mode has only one dimension argument.
        width_expr = parser.compile_filter(bits[2])
        height_expr = None
        # The leftovers are custom-attrs and the "as var" code, if they exist.
        leftovers = bits[3:]
    elif mode_string == 'height':
        # The width mode has only one dimension argument.
        width_expr = None
        height_expr = parser.compile_filter(bits[2])
        leftovers = bits[3:]
    else:
        # Other modes take two dimension arguments: width, then height.
        width_expr = parser.compile_filter(bits[2])
        height_expr = parser.compile_filter(bits[3])
        leftovers = bits[4:]

    attrs = {}
    output_var_name = None
    # If True, the next bit to be read is the output variable name.
    as_context = False
    # Set to False if any invalid formatting is detected.
    is_valid = True

    # Defined here because the same exception is used multiple times.
    error = template.TemplateSyntaxError(
        """
        '{0}' tag should be of the form
        {{% {0} self.photo 'max' 320 200 [ custom-attr="value" ... ] %}} or
        {{% {0} self.photo 'max' 320 200 as img %}} or
        {{% {0} self.photo 'width' 320 as img %}}.
        You CANNOT use both custom-attr="value" and 'as img'!
        """.format(tag_name)
    )

    for bit in leftovers:
        if bit == 'as':
            # Indicate that 'token' is of the form {% arbitrary_image self.photo 'max' 320 200 as img %}
            as_context = True
        elif as_context:
            if output_var_name is None:
                output_var_name = bit
            else:
                # More than one item exists after 'as' - reject as invalid.
                is_valid = False
        else:
            try:
                name, value = bit.split('=')
                # Resolve context variables as value.
                attrs[name] = parser.compile_filter(value)
            except ValueError:
                raise error

    if as_context and output_var_name is None:
        # Context was introduced but no variable given, which is invalid.
        is_valid = False

    if output_var_name and attrs:
        # Extra attrs are not valid when using the 'as img' form of the tag, because we can't include them in the
        # returned Rendition object.
        is_valid = False

    if is_valid:
        return node_class(
            image_expr, mode_expr, width_expr, height_expr, output_var_name=output_var_name, attrs=attrs
        )
    else:
        raise error
