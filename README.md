This is a collection of useful blocks and layouts for use within Wagtail's StreamField construct.


# Usage

**DEBUG** For now just install from the git repository and then add `jetstream` to your `INSTALLED_APPLICATIONS` in Django settings.

## Column Layouts

Use of the column layouts requires some boilerplate from the developer because Wagtail currently does not have a mechanism for determining a block's contents dynamically at runtime.

In the block declarations, subclass the desired block types as in the following example, adding to the column fields whichever blocks are desired to be added to the column's internal StreamField.


```
class TwoColumnBlock(BaseTwoColumnBlock):
    left_column = blocks.StreamBlock(
        COLUMN_PERMITTED_BLOCKS + [
            get_block_tuple(MyBlockType),
            ...
        ],
        icon='arrow-left',
        label='Left column content'
    )

    right_column = blocks.StreamBlock(
        COLUMN_PERMITTED_BLOCKS + [
            get_block_tuple(MyBlockType),
            ...
        ],
        icon='arrow-right',
        label='Right column content'
    )

```

## Block Types

**NOTE**: Some classes require custom javascript, so it is important to include `<script defer src="{% static 'jetstream/js/layouts.js' %}"></script>` somewhere on your page template.

Several image-related blocks, e.g. HeroImageCarouselBlock, use Bootstrap.js to implement their slideshow functionality. You'll need to install and load Bootstrap 4.1+ for that those to function.

We also assume that you are using jQuery 3.x and Moderizr.

**TODO**


# Helpers

### get_block_tuple()

Returns a standardized tuple of the block's class name and one of it's instances for use within the declarations of a StreamField's elements. This is useful when writing data migrations for the block because it allows the `type` field for each block to be standardized.

### BlockTupleMixin

A mixin class that, when included, allows the block to override the return of `get_block_tuple` for itself, allowing for customization of the block's listing type.
