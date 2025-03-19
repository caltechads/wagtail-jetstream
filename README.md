THIS PROJECT IS DEPRECATED. PLEASE DO NOT USE IT.
=================================================

This is a collection of useful blocks and layouts for use within Wagtail's StreamField.


# Usage

> This repository contains examples of some commonly requested blocks for
> Wagtail but it is ***NOT*** a complete, installable package. The best way to use
> this repository is as a place to find ideas.

> For example, if you want a Bootstrap image carousel that is editable as a
> StreamBlock, search blocks.py to locate a possible example. Copy this code
> into your own project. Please note that some higher level blocks include
> StructBlocks from elsewhere in blocks.py. Be sure to copy all the pieces you
> need - including the template and scss files.

> If you want a large number of blocks from this repository, please fork it and
> remove `FeatureCustomizedStreamBlock` and replace all uses of that block with
> Wagtail's own StreamBlock. This will remove the dependency on our unpublished
> `features.registry` and on CrequestMiddleware for determining the site from
> the request.

As of version 1.4, we no longer pre-compile the scss to css. Users are expected to run some sort of automatic sass compiler, like django-sass-processor, in order to compile the scss files.

As of version 2.0, the import paths only support Wagtail 3.0 or higher.

## Dependencies

- jQuery: [we use 3.3.1](https://code.jquery.com/jquery-3.3.1.min.js)
- Modernizr: [Customized version based on 3.6.0](https://modernizr.com/download/?cssanimations-csstransitions-addtest-mq-prefixed-prefixes-setclasses)
- Bootstrap:  [4.1.0](https://getbootstrap.com/docs/4.1/getting-started/introduction/)
- django-bleach: [>=0.3.0](https://pypi.org/project/django-bleach/)
- a SASS compiler. We use [django-compressor](https://pypi.org/project/django-compressor/) but whatever you currently use
  should work.

## Block Types

**NOTE**: Some classes require custom javascript, so you may need to include `<script defer src="{% static 'jetstream/js/layouts.js' %}"></script>` somewhere on your page template.

Several image-related blocks, e.g. HeroImageCarouselBlock, use Bootstrap.js to implement their slideshow functionality. You'll need to install and load Bootstrap 4.1+ for that those to function.

We also assume that you are using jQuery 3.x and Modernizr.

Example template fragment if you are using carousels or other blocks that depend
on Bootstrap:

```
{# Intentionally loaded synchronously, since its a prereq for other scripts_.. #}
<script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.1.3/dist/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>

{# This is a custom build of Modernizr created specifically for the features that we actually use in Multitenant. #}
<script defer src="{% static 'app-location/js/modernizr-3.5.0-custom.js' %}"></script>

<script defer src="{% static 'jetstream/js/utils.js' %}"></script>
<script defer src="{% static 'jetstream/js/layouts.js' %}"></script>
<!-- your other JS files here -->
{% endcompress %}
```


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

## Helpers

### get_block_tuple()

Returns a standardized tuple of the block's class name and one of it's instances for use within the declarations of a StreamField's elements. This is useful when writing data migrations for the block because it allows the `type` field for each block to be standardized.

### BlockTupleMixin

A mixin class that, when included, allows the block to override the return of
`get_block_tuple` for itself, allowing for customization of the block's listing
type. Primarily used so that TwoColumnBlock and BaseTwoColumnSubBlock can use
the same template files.
