from bs4 import BeautifulSoup
from collections import OrderedDict
from django import forms
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from wagtail import blocks, telepath
from wagtail.blocks import BaseStreamBlock
from wagtail.blocks.struct_block import StructBlockAdapter
from wagtail.models import Site
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from .templatetags.jetstream_tags import custom_bleach

try:
    # Imports the register_feature decorator from the 'features' module.
    from features.registry import register_feature, registry
except ImportError:
    # If features isn't installed, @register_feature becomes a noop, and the registry is empty.
    # noinspection PyUnusedLocal
    def register_feature(**kwargs):
        return lambda klass: klass
    registry = {'default': set(), 'special': set()}

from .utils import BACKGROUND_COLORS, FOREGROUND_COLORS, get_block_tuple, BlockTupleMixin

# =======
# Globals
# =======
wh_height_helptext = (
    'If "Fixed Dimensions" is checked, or if this block is placed outside a layout element (e.g. outside a N-Column "'
    'layout), set the image to be this many pixels tall.'
)

wh_width_helptext = (
    'If "Fixed Dimensions" is checked, or if this block is placed outside a layout element (e.g. outside a N-Column '
    'layout), set the image to be this many pixels wide.'
)


class UnknownBlockGroupError(Exception):
    pass


class FeatureCustomizedStreamBlock(blocks.StreamBlock):
    """
    This is a copy of FeatureCustomizedStreamBlock from Airspace. It lets us override the list of blocks presented
    to the user based on runtime information. We also sort the blocks differently.
    """

    # Because Block groups are not, themselves, anything except a string specified in the Meta class, we need some
    # method to tell the system what order to sort Groups in. This dictionary keys those Group strings to sort values.
    GROUP_SORT_VALUES = {
        # If a Block has no Group, its meta.group is ''. We want ungrouped blocks to appear first, so they get 0.
        '': 0,
        'Basic': 10,
        'Multimedia': 20,
        'Navigation': 30,
        'News & Calendar': 40,
        'Social Media': 50,
        'Misc': 60,
        'Special': 70,
    }

    def __init__(self, local_blocks=None, **kwargs):
        self._constructor_kwargs = kwargs

        # Note, this is calling BaseStreamBlock's super __init__, not FeatureCustomizedStreamBlock's. We don't want
        # BaseStreamBlock.__init__() to run, because it tries to assign to self.child_blocks, which it can't do because
        # we've overridden it with an @property. But we DO want Block.__init__() to run.
        super(BaseStreamBlock, self).__init__(**kwargs)

        # create a local (shallow) copy of base_blocks so that it can be supplemented by local_blocks
        self._child_blocks = self.base_blocks.copy()
        if local_blocks:
            for name, block in local_blocks:
                block.set_name(name)
                self._child_blocks[name] = block

        self._dependencies = self._child_blocks.values()

    @property
    def child_blocks(self):
        from djunk.middleware import get_current_request

        request = get_current_request()
        # Protect against crashing in case this ever runs outside of a request cycle.
        if request is None:
            return self._child_blocks

        # Protect against crashing of the site has no features (like the initial site built by Wagtail migration)
        # noinspection PyUnresolvedReferences
        try:
            features = Site.find_for_request(request).features
            return OrderedDict([
                item for item in self._child_blocks.items() if features.feature_is_enabled(item[0])
            ])
        except Site.features.RelatedObjectDoesNotExist:
            return self._child_blocks

    @property
    def dependencies(self):
        from djunk.middleware import get_current_request

        request = get_current_request()
        # Protect against crashing in case this ever runs outside of a request cycle.
        if request is None:
            return self._child_blocks

        # Protect against crashing of the site has no features (like the initial site built by Wagtail migration)
        # noinspection PyUnresolvedReferences
        try:
            features = Site.find_for_request(request).features
            return [block for block in self._dependencies if features.feature_is_enabled(block.name)]
        except Site.features.RelatedObjectDoesNotExist:
            return self._child_blocks

    def sorted_child_blocks(self):
        """
        Child blocks, sorted by label, and then sorted again by group, in the order specified in GROUP_SORT_VALUES.
        This puts them in alphabetical order within each group segment.
        """
        def sort_groups(child_block):
            try:
                return self.GROUP_SORT_VALUES[child_block.meta.group]
            except KeyError:
                # If a Block has an unknown Group, we can't sort it. So we throw a descriptive error, which makes it
                # clear what needs to be done to fix it.
                raise UnknownBlockGroupError(
                    f'The group "{child_block.meta.group}" is not in FeatureCustomizedStreamBlock.GROUP_SORT_VALUES.'
                    f' Please either rename the group to match that the ones in that dict, or add'
                    f' "{child_block.meta.group}" to it.'
                )

        child_blocks = sorted(self.child_blocks.values(), key=lambda child_block: child_block.meta.label)
        return sorted(child_blocks, key=sort_groups)


# ====================
# Component Sub-blocks
# ====================
class IntegerChoiceBlock(blocks.ChoiceBlock):
    """
    A ChoiceBlock for integers only. Using this instead of ChoiceBlock ensures that the value retrieved from the
    field is an integer instead of a string.
    """

    def to_python(self, value):
        return int(value)

    def get_prep_value(self, value):
        return int(value)

    def value_from_form(self, value):
        return int(value)


class LinkBlock(blocks.StructBlock):
    """
    Allows a user to optionally link the containing block to a Page, a Document, or a relative or absolute URL.

    NOTE: Due to limitations in CSS, callers of LinkBlock() must not specify a label in the construction arguments.
    See the comment in the Meta class for why.

    NOTE: Within a template, checking for the existence of `self.link` will always return True because the LinkBlock
    object is not falsy, even if it has no contents. To retrieve the value of a LinkBlock, use the {% link_url %}
    template tag from jetstream_tags. ex:
        {% load jetstream_tags %}
        {% link_url self.link as url %}
        {% if url %}
            <a href={{ url }}></a>
        {% endif %}
    """
    page = blocks.PageChooserBlock(
        required=False,
        help_text="Link to the chosen page. If a Page is selected, it will take precedence over both."
    )
    document = DocumentChooserBlock(
        required=False,
        help_text="Link to the chosen document. If a document is selected, it will take precedence over a URL."
    )
    url = blocks.CharBlock(
        required=False,
        help_text="Link to the given URL. This can be a relative URL to a location your own site (e.g. /example-page) "
                  "or an absolute URL to a page on another site (e.g. http://www.caltech.edu). Note: absolute URLs "
                  "must include the http:// otherwise they will not work."
    )

    class Meta:
        label = 'Link'
        form_classname = 'link-block'
        # Does not need a Group


class DimensionsOptionsBlock(blocks.StructBlock):
    """
    Allows the user to specify arbitrary dimensions for a block that has certain interactions with
    the various column layouts.
    """
    use = blocks.BooleanBlock(
        default=False,
        required=False,
        label='Use Fixed Dimensions',
        help_text="Normally, the image will expand its height to satisfy the suggested height on its parent block. "
                  "Checking this box will make it conform to the specified height and width, instead."
    )
    height = blocks.IntegerBlock(
        default=200,
        label="Height (pixels)",
        help_text=wh_height_helptext
    )
    width = blocks.IntegerBlock(
        default=200,
        label="Width (pixels)",
        help_text=wh_width_helptext
    )

    class Meta:
        form_classname = 'dimensions-options struct-block'
        # Don't display a label for this block. Our override of wagtailadmin/block_forms/struct.html obeys this flag.
        no_label = True


class DimensionsOptionsBlockAdapter(StructBlockAdapter):
    """
    DimensionsOptionsBlock is a StructBlock with extra form-side functionality. So, we use StructBlockAdapter as the
    base class, and override only the js_constructor and media. Alongside our custom javascript file, which subclasses
    wagtailStreamField.blocks.StructBlockDefinition, this lets us add our custom javascript behavior.
    """
    js_constructor = 'jetstream.DimensionsOptionsBlock'

    @cached_property
    def media(self):
        structblock_media = super().media
        return forms.Media(
            js=structblock_media._js + ['jetstream/js/admin/dimensions-options-telepath.js'],
            css=structblock_media._css
        )


telepath.register(DimensionsOptionsBlockAdapter(), DimensionsOptionsBlock)


class BackgroundOptionsBlock(blocks.StructBlock):
    background_image = ImageChooserBlock(
        required=False,
        help_text="This image, if supplied, will appear as a background for this block"
    )
    background_color = blocks.ChoiceBlock(
        choices=BACKGROUND_COLORS,
        blank=False,
        required=False,
        default=BACKGROUND_COLORS[0],
        help_text="Set the background color of this block.  If a Background Image is also supplied, the Background "
                  "Image will be displayed instead of this color"
    )

    class Meta:
        form_classname = 'color-options struct-block'
        # Don't display a label for this block. Our override of wagtailadmin/block_forms/struct.html obeys this flag.
        no_label = True


class ActionButtonBlock(blocks.StructBlock):
    STYLES = (
        ('btn-primary', 'Primary'),
        ('btn-light', 'Default'),
        ('btn-link', 'Info'),
    )

    text = blocks.TextBlock()
    link = LinkBlock()
    style = blocks.ChoiceBlock(
        choices=[(style[0], style[1]) for style in STYLES],
        default=STYLES[0][0]
    )

    class Meta:
        label = 'Action Button'
        template = 'jetstream/blocks/action_button_block.html'
        form_classname = 'action-button-block struct-block'
        icon = 'form'


class ActionButtonBarBlock(blocks.StructBlock):
    CHOICES = (
        ('center-block', 'Center'),
        ('left-align-block', 'Align Left'),
        ('right-align-block', 'Align Right')
    )

    alignment = blocks.ChoiceBlock(
        choices=[(choice[0], choice[1]) for choice in CHOICES],
        default=CHOICES[0][0],
    )
    actions = blocks.ListBlock(
        ActionButtonBlock(),
        default=[]
    )

    class Meta:
        label = 'Action Button Bar'
        template = 'jetstream/blocks/action_button_bar_block.html'
        form_classname = 'action-button-bar struct-block'
        icon = 'form'
        # Does not need a Group


class ColorOptionsBlock(blocks.StructBlock):
    background_image = ImageChooserBlock(
        required=False,
        help_text="This image, if supplied, will appear as a background for this block"
    )
    background_color = blocks.ChoiceBlock(
        choices=BACKGROUND_COLORS,
        blank=False,
        required=False,
        default=BACKGROUND_COLORS[0],
        help_text="Set the background color of this block.  If a Background Image is also supplied, the Background "
                  "Image will be displayed instead of this color"
    )
    text_color = blocks.ChoiceBlock(
        choices=FOREGROUND_COLORS,
        blank=False,
        required=False,
        default=FOREGROUND_COLORS[0],
        help_text="Set the color for the text in this block. This is here so you can make your text visible on both "
                  "light and dark backgrounds."
    )

    class Meta:
        form_classname = 'color-options struct-block'
        # Don't display a label for this block. Our override of wagtailadmin/block_forms/struct.html obeys this flag.
        no_label = True


class RelatedLinksNodeBlock(blocks.StructBlock):
    text = blocks.CharBlock(required=True)
    link = LinkBlock()

    class Meta:
        template = 'jetstream/blocks/related_link.html'


# ======================================================================================================
# ====================================== MEDIA BLOCKS ==================================================
# ======================================================================================================
@register_feature(feature_type='default')
class ImagePanelBlock(blocks.StructBlock, BlockTupleMixin):
    STYLES = (
        ('link', 'Image Link', 'jetstream/blocks/image_panel_block-link.html', []),
        ('captioned', 'Image w/ Caption', 'jetstream/blocks/image_panel_block-caption.html', []),
        ('rollover', 'Image Link w/ Rollover Text', 'jetstream/blocks/image_panel_block-rollover.html', []),
        ('separate_text', 'Image Card (Equal Heights)', 'jetstream/blocks/image_panel_block-card.html', ['equal']),
        ('separate_text_natural', 'Image Card (Natural Heights)', 'jetstream/blocks/image_panel_block-card.html', ['natural']),  # noqa
        ('image_listing_left', 'Listing (Image Left)', 'jetstream/blocks/image_panel_block-listing.html', ['left']),
        ('image_listing_right', 'Listing (Image Right)', 'jetstream/blocks/image_panel_block-listing.html', ['right']),
    )

    image = ImageChooserBlock()
    style = blocks.ChoiceBlock(choices=[(style[0], style[1]) for style in STYLES], default='link')
    title = blocks.CharBlock(required=False)
    desc = blocks.CharBlock(
        required=False,
        label='Body'
    )
    display_caption = blocks.BooleanBlock(
        label='Display Caption',
        help_text='Check this box to display the caption and photo credit below this image.',
        required=False,
        default=False
    )
    link = LinkBlock()
    fixed_dimensions = DimensionsOptionsBlock()

    class Meta:
        label = 'Image Panel'
        form_classname = 'image-panel struct-block'
        icon = 'image'
        group = 'Multimedia'

    def render(self, value, context=None):
        """
        We override this method to allow a template to be chosen dynamically based on the value of the "style" field.
        """
        style_to_template_map = {style[0]: (style[2], style[3]) for style in self.STYLES}
        try:
            (template, extra_classes) = style_to_template_map[value['style']]
        except KeyError:
            # If this block somehow doesn't have a known style, fall back to the basic_render() method.
            return self.render_basic(value, context=context)

        new_context = self.get_context(value, parent_context=context if context is None else dict(context))
        new_context['extra_classes'] = " ".join(extra_classes)
        return mark_safe(render_to_string(template, new_context))


class ImagePanelBlockAdapter(StructBlockAdapter):
    """
    ImagePanelBlock is a StructBlock with extra form-side functionality. So, we use StructBlockAdapter as the base
    class, and override only the js_constructor and media. Alongside our custom javascript file, which subclasses
    wagtailStreamField.blocks.StructBlockDefinition, this lets us add our custom javascript behavior.
    """
    js_constructor = 'jetstream.ImagePanelBlock'

    @cached_property
    def media(self):
        structblock_media = super().media
        return forms.Media(
            js=structblock_media._js + ['jetstream/js/admin/image-panel-telepath.js'],
            css=structblock_media._css
        )


telepath.register(ImagePanelBlockAdapter(), ImagePanelBlock)


@register_feature(feature_type='default')
class HeroImageBlock(blocks.StructBlock, BlockTupleMixin):

    style = blocks.ChoiceBlock(
        choices=[
            ('regular-width', 'Regular Width'),
            ('full-width', 'Full Width')
        ],
        default='regular-width',
        label='Overall style',
        help_text=('Regular Width fills the normal page area. '
                   'Full Width fills the entire width of the browser. Shorter images will be tiled.')
    )
    text_style = blocks.ChoiceBlock(
        choices=[
            ('bare-serif', 'Bare text w/ serif font'),
            ('bare-sans-serif', 'Bare text w/ sans-serif font'),
            ('white-translucent-serif', 'White translucent background behind serif text'),
            ('white-translucent-sans-serif', 'White translucent background behind sans-serif text'),
        ],
        default='white-translucent-serif',
        label='Text style'
    )
    image = ImageChooserBlock()
    title = blocks.CharBlock(required=False)
    desc = blocks.RichTextBlock(
        required=False,
        label='Text'
    )
    height = blocks.IntegerBlock(
        default=500,
        label='Height (pixels)'
    )
    position = blocks.ChoiceBlock(
        choices=[
            ('position-top-left', 'Top Left'),
            ('position-top-middle', 'Top Middle'),
            ('position-top-right', 'Top Right'),
            ('position-left', 'Left'),
            ('position-middle', 'Middle'),
            ('position-right', 'Right'),
            ('position-bottom-left', 'Bottom Left'),
            ('position-bottom-middle', 'Bottom Middle'),
            ('position-bottom-right', 'Bottom Right'),
        ],
        default='position-middle',
        label='Text Position'
    )
    actions = ActionButtonBarBlock(
        label='Action Buttons',
        required=False
    )

    class Meta:
        label = 'Hero Image'
        template = 'jetstream/blocks/hero_image_block.html'
        form_classname = 'hero-image struct-block'
        icon = 'image'
        group = 'Multimedia'


@register_feature(feature_type='default')
class HeroImageCarouselBlock(blocks.StructBlock, BlockTupleMixin):

    slides = blocks.ListBlock(
        blocks.StructBlock([
            ('image', ImageChooserBlock()),
            ('title', blocks.CharBlock(required=False)),
            ('text', blocks.TextBlock(required=False)),
            ('link', LinkBlock()),
        ])
    )
    height = blocks.IntegerBlock(
        default=300,
        label="Hero Image Height (pixels)",
    )
    width = blocks.IntegerBlock(
        default=1000,
        label="Hero Image Width (pixels)",
    )
    cycle_timeout = blocks.IntegerBlock(
        default=10000,
        help_text="The time between automatic image cycles (in milliseconds). Set to 0 to disable automatic cycling."
    )

    class Meta:
        template = 'jetstream/blocks/hero_image_carousel_block.html'
        form_classname = 'image-carousel struct-block'
        label = 'Hero Image Slider'
        icon = 'image'
        group = 'Multimedia'


@register_feature(feature_type='default')
class ImageCarouselBlock(blocks.StructBlock, BlockTupleMixin):

    header = blocks.TextBlock(required=False)
    slides = blocks.ListBlock(
        blocks.StructBlock([
            ('image', ImageChooserBlock()),
            ('text', blocks.CharBlock(required=False)),
            ('link', LinkBlock()),
        ])
    )
    cycle_timeout = blocks.IntegerBlock(
        default=5000,
        help_text="The time between automatic image cycles (in milliseconds). Set to 0 to disable automatic cycling."
    )

    class Meta:
        template = 'jetstream/blocks/image_carousel_block.html'
        label = 'Image Carousel'
        icon = 'image'
        group = 'Multimedia'


@register_feature(feature_type='default')
class ImageGalleryBlock(blocks.StructBlock, BlockTupleMixin):
    """
    Renders an Image Gallery in a variety of styles.
    """
    STYLES = (
        ('gallery', 'Image Gallery', 'jetstream/blocks/image_gallery_block-gallery.html', []),
        ('slider', 'Image Slider w/ Thumbnail Picker', 'jetstream/blocks/image_gallery_block-slider.html', []),
    )
    # Only factors of 12 are allowed, because we use a 12-column layout.
    COLUMN_CHOICES = [(1, 1), (2, 2), (3, 3), (4, 4), (6, 6)]

    style = blocks.ChoiceBlock(choices=[(style[0], style[1]) for style in STYLES], default='gallery')
    columns = IntegerChoiceBlock(choices=COLUMN_CHOICES, default=3)
    height = blocks.IntegerBlock(
        default=300,
        label='Height (pixels)',
        help_text="Images' widths will be scaled with the number of columns. This field determines their height."
    )
    images = blocks.ListBlock(
        ImageChooserBlock(label='Image')
    )

    class Meta:
        label = 'Image Gallery'
        form_classname = 'image-gallery struct-block'
        icon = 'image'
        group = 'Multimedia'

    def render(self, value, context=None):
        """
        We override this method to allow a template to be chosen dynamically based on the value of the "style" field.
        """
        style_to_template_map = {style[0]: (style[2], style[3]) for style in self.STYLES}
        try:
            (template, extra_classes) = style_to_template_map[value['style']]
        except KeyError:
            # If this block somehow doesn't have a known style, fall back to the basic_render() method.
            return self.render_basic(value, context=context)

        new_context = self.get_context(value, parent_context=context if context is None else dict(context))
        new_context['extra_classes'] = " ".join(extra_classes)
        new_context['bootstrap_column_width'] = int(12 / value['columns'])
        return mark_safe(render_to_string(template, new_context))


class ImageGalleryBlockAdapter(StructBlockAdapter):
    """
    ImageGalleryBlock is a StructBlock with extra form-side functionality. So, we use StructBlockAdapter as the base
    class, and override only the js_constructor and media. Alongside our custom javascript file, which subclasses
    wagtailStreamField.blocks.StructBlockDefinition, this lets us add our custom javascript behavior.
    """
    js_constructor = 'jetstream.ImageGalleryBlock'

    @cached_property
    def media(self):
        structblock_media = super().media
        return forms.Media(
            js=structblock_media._js + ['jetstream/js/admin/image-gallery-telepath.js'],
            css=structblock_media._css
        )


telepath.register(ImageGalleryBlockAdapter(), ImageGalleryBlock)


@register_feature(feature_type='default')
class SpacerBlock(blocks.StructBlock, BlockTupleMixin):

    height = IntegerChoiceBlock(
        choices=[
            (12, 12),
            (20, 20),
            (25, 25),
            (30, 30),
            (40, 40),
            (50, 50),
            (75, 75),
            (100, 100),
            (125, 125),
            (150, 150),
            (175, 175),
            (200, 200),
            (225, 225),
            (250, 250)
        ],
        blank=False,
        default=25,
        label="Height (pixels)",
        help_text="Add empty vertical space whose height is this many pixels.")

    class Meta:
        label = 'Spacer'
        template = 'jetstream/blocks/spacer_block.html'
        form_classname = 'spacer struct-block'
        icon = 'arrows-up-down'
        group = 'Basic'


@register_feature(feature_type='default')
class RelatedLinksBlock(blocks.StructBlock, BlockTupleMixin):
    title = blocks.CharBlock(
        required=False,
        label='Title',
    )
    links = blocks.ListBlock(
        RelatedLinksNodeBlock(label='Link'),
        label='Links'
    )
    color = ColorOptionsBlock()
    fixed_dimensions = DimensionsOptionsBlock()

    class Meta:
        label = 'Related Links'
        template = 'jetstream/blocks/related_links_block.html'
        form_classname = 'related-links struct-block'
        icon = 'list-ul'
        group = 'Navigation'


@register_feature(feature_type='default')
class VideoBlock(blocks.StructBlock, BlockTupleMixin):

    video = EmbedBlock(
        label="Video Embed URL",
        help_text="Paste the video URL from YouTube or Vimeo. e.g. https://www.youtube.com/watch?v=l3Pz_xQZVDg "
                  "or https://vimeo.com/207076450."
    )
    title = blocks.CharBlock(required=False)

    fixed_dimensions = DimensionsOptionsBlock()

    class Meta:
        label = 'Video w/ Title'
        template = 'jetstream/blocks/video_block.tpl'
        form_classname = 'video-block struct-block'
        icon = 'media'
        group = 'Multimedia'


@register_feature(feature_type='default')
class SectionTitleBlock(blocks.StructBlock, BlockTupleMixin):
    STYLES = {
        'section_divider': 'jetstream/blocks/section_title-section_divider.html',
        'block_header': 'jetstream/blocks/section_title-block_header.html'
    }

    text = blocks.CharBlock(required=True)
    style = blocks.ChoiceBlock(
        choices=[
            ('section_divider', 'Section Divider'),
            ('block_header', 'Block Header'),
        ],
        requried=True,
        blank=False,
        default='section_divider'
    )

    def render(self, value, context=None):
        """
        Uses the appropriate template to render this block, based on the 'style' value.
        """
        try:
            template = self.STYLES[value['style']]
        except KeyError:
            # If this block somehow doesn't have a known style, fall back to the basic_render() method.
            return self.render_basic(value, context=context)

        new_context = self.get_context(value, parent_context=context if context is None else dict(context))
        return mark_safe(render_to_string(template, new_context))

    class Meta:
        form_classname = 'section-title struct-block'
        label = 'Section Title'
        icon = 'form'
        group = 'Basic'


@register_feature(feature_type='default')
class MenuListingBlock(blocks.StructBlock, BlockTupleMixin):

    title = blocks.CharBlock(
        required=False,
        help_text="If supplied, display this at the top of the menu listing"
    )
    show = blocks.ChoiceBlock(
        choices=[
            ('siblings', 'Page Siblings'),
            ('children', 'Page Children')
        ],
        blank=False,
        default='siblings',
        help_text='"Page Siblings" lists all pages at the same level of the site page hierarchy as this page; '
                  '"Page Children" lists all pages that are directly below this page in the page hierarchy.'
    )
    color = ColorOptionsBlock()
    fixed_dimensions = DimensionsOptionsBlock()

    class Meta:
        template = 'jetstream/blocks/menu_listing_block.html'
        form_classname = 'menu-listing struct-block'
        label = 'Menu Section'
        icon = 'list-ul'
        group = 'Navigation'


@register_feature(feature_type='default')
class FancyRichTextBlock(blocks.StructBlock, BlockTupleMixin):

    text = blocks.RichTextBlock(
        required=True,
        label="Body"
    )
    color = ColorOptionsBlock()
    fixed_dimensions = DimensionsOptionsBlock()

    class Meta:
        template = 'jetstream/blocks/fancy_rich_text_block.html'
        form_classname = 'fancy-richtext struct-block'
        label = 'Rich Text'
        icon = 'doc-full'
        group = 'Basic'


@register_feature(feature_type='default')
class CalloutBlock(blocks.StructBlock, BlockTupleMixin):
    """
    CalloutBlock is for those Divisions-style grid blocks that have a solid background color, a title, and a blurb.
    They should not be able to be placed at the top level; they only belong inside a column layout.
    """

    title = blocks.CharBlock(
        required=True,
        max_length=100
    )
    body = blocks.RichTextBlock(
        required=True
    )
    color = ColorOptionsBlock()
    fixed_dimensions = DimensionsOptionsBlock()

    class Meta:
        template = 'jetstream/blocks/callout_block.html'
        form_classname = 'callout struct-block'
        label = 'Callout'
        icon = 'doc-full'
        group = 'Misc'


class IFrameBlock(blocks.CharBlock, BlockTupleMixin):
    """
    We need a custom field as a place to add a validation. Originally we just used a CharBlock directly,
    but then you could put anything in here - including script tags.
    """
    class Meta:
        label = 'iFrame'
        template = 'jetstream/blocks/iframe_block.html'
        form_classname = 'iframe-block struct-block'
        icon = 'media'
        # Does not need a Group

    def clean(self, value):
        """
        Parse the iframe data submitted and then rebuild the tag using only the allowed attributes.
        For browsers that do not support iframes, we allow a subset of tags inside the iframe contents.
        """
        soup = BeautifulSoup(value, "lxml")
        iframe = soup.find('iframe')
        if not iframe:
            raise ValidationError(_("The embed string needs to look like '<iframe ...></iframe>'"))

        contents = ' '.join(str(item) for item in iframe.contents) if iframe.contents else ''
        contents = custom_bleach(contents, "a,b,i,em,strong,br,sup,sub")
        # I am allowing the standards compliant tags listed on
        # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe
        # plus 'frameborder' - in case someone actually wants a border around their embed
        allowed_tags = ['allowfullscreen', 'height', 'width', 'name', 'referrerpolicy', 'sandbox', 'src',
                        'title', 'width', 'frameborder']
        tag = "<iframe"
        for attr in iframe.attrs.keys():
            if attr in allowed_tags:
                tag += ' {0}="{1}"'.format(attr, iframe.attrs[attr])
        tag += ' scrolling="auto">{0}</iframe>'.format(contents)

        return tag


@register_feature(feature_type='special')
class IFrameEmbedBlock(blocks.StructBlock, BlockTupleMixin):
    """
    Offer users the ability to use iframes.
    BECAUSE this is a 'special feature' we can restrict which sites are allowed to use them.
    """
    html = IFrameBlock(
        help_text=escape(
            "Paste the iFrame from your provider here. e.g.  "
            '<iframe height="300px" frameborder="0" style="padding: 25px 10px;"'
            ' src="https://user.wufoo.com/embed/z1qnwrlw1iefzsu/">'
            '  <a href="https://user.wufoo.com/forms/z1qnwrlw1iefzsu/">Fill out my Wufoo form! </a>'
            '</iframe>'
        )
    )

    fixed_dimensions = DimensionsOptionsBlock()

    class Meta:
        label = 'iFrame'
        template = 'jetstream/blocks/iframe_block.html'
        form_classname = 'iframe-block struct-block'
        icon = 'media'
        group = 'Special'


###############################################################################
########################### LAYOUT BLOCK TYPES ################################
###############################################################################
# These go at the end because they need to include all of the content blocks defined above.
COLUMN_PERMITTED_BLOCKS = [
    get_block_tuple(FancyRichTextBlock()),
    get_block_tuple(CalloutBlock()),
    get_block_tuple(ImageCarouselBlock()),
    get_block_tuple(ImageGalleryBlock()),
    get_block_tuple(RelatedLinksBlock()),
    get_block_tuple(ImagePanelBlock()),
    get_block_tuple(VideoBlock()),
    get_block_tuple(IFrameEmbedBlock()),
    get_block_tuple(SectionTitleBlock()),
    get_block_tuple(MenuListingBlock()),
    get_block_tuple(SpacerBlock()),
]

# Choices for col-md-## class used by bootstrap for grids
BS_COL_CHOICES = [(x, x) for x in range(1, 12)]
col_helptext = "Column width is represented as units out of twelve. EX. 6 / 12 units will take up half the container."
fixed_height_helptext = (
    "Blocks that contain images that are placed in one of the columns here will set themselves to this height unless "
    "specifically overridden on the block."
)


class BaseTwoColumnSubBlock(blocks.StructBlock, BlockTupleMixin):
    """
    Duplicate of BaseTwoColumnBlock without the sub block to avoid recursion.
    """
    left_column_width = IntegerChoiceBlock(choices=BS_COL_CHOICES, blank=False, default=6, help_text=col_helptext)

    fixed_height = blocks.IntegerBlock(
        default=350,
        label="Suggested height for contained widgets",
        help_text="Blocks that contain images that are placed in one of the columns here will set themselves to this "
                  "height unless specifically overridden on the block."
    )
    gutter_width = IntegerChoiceBlock(
        choices=[(0, 0), (12, 12), (20, 20), (30, 30), (40, 40)],
        blank=False,
        default=12,
        label="Column Gutter Width (pixels)",
        help_text="This determines how wide the spacing between columns will be, in pixels."
    )
    background = BackgroundOptionsBlock()
    left_column = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-left',
        label='Left column content',
        required=False
    )
    right_column = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-right',
        label='Right column content',
        required=False
    )

    class Meta:
        label = 'Two Columns'
        template = 'jetstream/blocks/layout/two_column_block.html'
        form_classname = 'layout-two-column-sub struct-block'
        group = 'Basic'

    @classmethod
    def get_block_machine_name(cls):
        """
        Overrides this method from BlockTupleMixin so that we use the same machine name as BaseTwoColumnBlock.
        """
        return 'two_column_layout'

    def get_block_tuple(self):
        """
        Overrides this method from BlockTupleMixin so that we use the same machine name as BaseTwoColumnBlock.
        """
        return ('two_column_layout', self)


class BaseTwoColumnBlock(blocks.StructBlock, BlockTupleMixin):
    """
    Base class to be overridden in implementing sub module with boilerplate implementation of column layout.
    """
    STYLES = (
        ('regular-width', 'Regular Width'),
        ('full-width', 'Full Width'),
        ('regular-width padded', 'Regular Width, Padded'),
        ('full-width padded', 'Full Width, Padded')
    )
    style = blocks.ChoiceBlock(choices=[(style[0], style[1]) for style in STYLES], default=STYLES[0][0])
    left_column_width = IntegerChoiceBlock(choices=BS_COL_CHOICES, blank=False, default=6, help_text=col_helptext)
    fixed_height = blocks.IntegerBlock(
        default=350,
        label="Suggested height for contained widgets",
        help_text=fixed_height_helptext
    )
    gutter_width = IntegerChoiceBlock(
        choices=[(0, 0), (12, 12), (20, 20), (30, 30), (40, 40)],
        blank=False,
        default=12,
        label="Column Gutter Width (pixels)",
        help_text="This determines how wide the spacing between columns will be, in pixels."
    )
    background = BackgroundOptionsBlock()
    left_column = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-left',
        label='Left column content',
        required=False
    )

    right_column = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-right',
        label='Right column content',
        required=False
    )

    class Meta:
        label = 'Two Columns'
        template = 'jetstream/blocks/layout/two_column_block.html'
        form_classname = 'layout-two-column struct-block'
        group = 'Basic'

    @classmethod
    def get_block_machine_name(cls):
        """
        Overrides this method from BlockTupleMixin so that we use the same machine name as BaseTwoColumnSubBlock.
        """
        return 'two_column_layout'

    def get_block_tuple(self):
        """
        Overrides this method from BlockTupleMixin so that we use the same machine name as BaseTwoColumnSubBlock.
        """
        return ('two_column_layout', self)


class BaseThreeColumnSubBlock(blocks.StructBlock, BlockTupleMixin):
    """
    Duplicate of BaseThreeColumnBlock without the sub block to avoid recursion.
    """
    left_column = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-left',
        label='Left column content',
        required=False
    )
    middle_column = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-right',
        label='Middle column content',
        required=False
    )
    right_column = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-right',
        label='Right column content',
        required=False
    )

    left_column_width = IntegerChoiceBlock(choices=BS_COL_CHOICES, blank=False, default=4, help_text=col_helptext)
    right_column_width = IntegerChoiceBlock(choices=BS_COL_CHOICES, blank=False, default=4, help_text=col_helptext)

    fixed_height = blocks.IntegerBlock(
        default=300,
        label="Suggested height for contained widgets",
        help_text=fixed_height_helptext
    )
    gutter_width = IntegerChoiceBlock(
        choices=[(0, 0), (12, 12), (20, 20), (30, 30), (40, 40)],
        blank=False,
        default=12,
        label="Column Gutter Width (pixels)",
        help_text="This determines how wide the spacing between columns will be, in pixels."
    )
    background = BackgroundOptionsBlock()

    class Meta:
        label = 'Three Columns'
        template = 'jetstream/blocks/layout/three_column_block.html'
        form_classname = 'layout-three-column-sub struct-block'
        group = 'Basic'

    @classmethod
    def get_block_machine_name(cls):
        """
        Overrides this method from BlockTupleMixin so that we use the same machine name as BaseThreeColumnSubBlock.
        """
        return 'three_column_layout'

    def get_block_tuple(self):
        """
        Overrides this method from BlockTupleMixin so that we use the same machine name as BaseThreeColumnSubBlock.
        """
        return ('three_column_layout', self)


class BaseThreeColumnBlock(blocks.StructBlock, BlockTupleMixin):
    STYLES = (
        ('regular-width', 'Regular Width'),
        ('full-width', 'Full Width'),
        ('regular-width padded', 'Regular Width, Padded'),
        ('full-width padded', 'Full Width, Padded')
    )

    style = blocks.ChoiceBlock(choices=[(style[0], style[1]) for style in STYLES], default=STYLES[0][0])
    left_column_width = IntegerChoiceBlock(choices=BS_COL_CHOICES, blank=False, default=4, help_text=col_helptext)
    right_column_width = IntegerChoiceBlock(choices=BS_COL_CHOICES, blank=False, default=4, help_text=col_helptext)
    fixed_height = blocks.IntegerBlock(
        default=300,
        label="Suggested height for contained widgets",
        help_text=fixed_height_helptext
    )
    gutter_width = IntegerChoiceBlock(
        choices=[(0, 0), (12, 12), (20, 20), (30, 30), (40, 40)],
        blank=False,
        default=12,
        label="Column Gutter Width (pixels)",
        help_text="This determines how wide the spacing between columns will be, in pixels."
    )
    background = BackgroundOptionsBlock()
    left_column = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-left',
        label='Left column content',
        required=False
    )

    middle_column = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-right',
        label='Middle column content',
        required=False
    )

    right_column = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-right',
        label='Right column content',
        required=False
    )

    class Meta:
        label = 'Three Columns'
        template = 'jetstream/blocks/layout/three_column_block.html'
        form_classname = 'layout-three-column struct-block'
        group = 'Basic'

    @classmethod
    def get_block_machine_name(cls):
        """
        Overrides this method from BlockTupleMixin so that we use the same machine name as ThreeColumnSubBlock.
        """
        return 'three_column_layout'

    def get_block_tuple(self):
        """
        Overrides this method from BlockTupleMixin so that we use the same machine name as ThreeColumnSubBlock.
        """
        return ('three_column_layout', self)


class BaseFourColumnBlock(blocks.StructBlock, BlockTupleMixin):
    STYLES = (
        ('regular-width', 'Regular Width'),
        ('full-width', 'Full Width'),
        ('regular-width padded', 'Regular Width, Padded'),
        ('full-width padded', 'Full Width, Padded')
    )

    style = blocks.ChoiceBlock(choices=[(style[0], style[1]) for style in STYLES], default=STYLES[0][0])
    column_one_width = IntegerChoiceBlock(choices=BS_COL_CHOICES, blank=False, default=3, help_text=col_helptext)
    column_two_width = IntegerChoiceBlock(choices=BS_COL_CHOICES, blank=False, default=3, help_text=col_helptext)
    column_three_width = IntegerChoiceBlock(choices=BS_COL_CHOICES, blank=False, default=3, help_text=col_helptext)
    fixed_height = blocks.IntegerBlock(
        default=250,
        label="Suggested height for contained widgets",
        help_text=fixed_height_helptext
    )
    gutter_width = IntegerChoiceBlock(
        choices=[(0, 0), (12, 12), (20, 20), (30, 30), (40, 40)],
        blank=False,
        default=12,
        label="Column Gutter Width (pixels)",
        help_text="This determines how wide the spacing between columns will be, in pixels."
    )
    background = BackgroundOptionsBlock()
    column_one = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        label='Column One Content',
        required=False
    )
    column_two = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        label='Column Two Content',
        required=False
    )
    column_three = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        label='Column Three Content',
        required=False
    )
    column_four = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        label='Column Four Content',
        required=False
    )

    class Meta:
        label = 'Four Columns'
        template = 'jetstream/blocks/layout/four_column_block.html'
        form_classname = 'layout-four-column struct-block'
        group = 'Basic'

    @classmethod
    def get_block_machine_name(cls):
        """
        Overrides this method from BlockTupleMixin so that we use the legacy machine name.
        """
        return 'four_column_layout'

    def get_block_tuple(self):
        """
        Overrides this method from BlockTupleMixin so that we use the legacy machine name.
        """
        return ('four_column_layout', self)


class BaseSidebarLayoutBlock(blocks.StructBlock, BlockTupleMixin):
    text = blocks.RichTextBlock()
    sidebar = FeatureCustomizedStreamBlock(
        COLUMN_PERMITTED_BLOCKS,
        icon='arrow-right',
        label='Sidebar',
        required=False
    )
    sidebar_width = IntegerChoiceBlock(choices=BS_COL_CHOICES, blank=False, default=4, help_text=col_helptext)
    sidebar_alignment = blocks.ChoiceBlock(choices=[('left', 'Left'), ('right', 'Right')], blank=False, default='left')
    fixed_height = blocks.IntegerBlock(
        default=250,
        label="Suggested height for child widgets",
        help_text=(
            "Child blocks containing images will set themselves to this height unless specifically overridden on the "
            "block. Set this to 0 to not enforce a height."
        )
    )

    class Meta:
        label = 'Sidebar Layout'
        template = 'jetstream/blocks/layout/sidebar_layout_block.html'
        form_classname = 'layout-sidebar struct-block'
        group = 'Basic'
