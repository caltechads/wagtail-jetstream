from wagtail.blocks import Block
from wagtail.fields import StreamField

from jetstream.blocks import FeatureCustomizedStreamBlock


class FeatureCustomizedStreamField(StreamField):

    def __init__(self, block_types, use_json_field=None, **kwargs):
        # extract kwargs that are to be passed on to the block, not handled by super
        block_opts = {}
        for arg in ["min_num", "max_num", "block_counts", "collapsed"]:
            if arg in kwargs:
                block_opts[arg] = kwargs.pop(arg)

        # for a top-level block, the 'blank' kwarg (defaulting to False) always overrides the
        # block's own 'required' meta attribute, even if not passed explicitly; this ensures
        # that the field and block have consistent definitions
        block_opts["required"] = not kwargs.get("blank", False)

        # This calls Field.__init__(), NOT StreamField.__init__(). We do this because this override's purpose is
        # to skip StreamField.__init__() so we can _replace_ it's code with our own, rather than supplement it.
        super(StreamField, self).__init__(**kwargs)

        self.use_json_field = use_json_field

        if isinstance(block_types, Block):
            # use the passed block as the top-level block
            self.stream_block = block_types
        elif isinstance(block_types, type):
            # block passed as a class - instantiate it
            self.stream_block = block_types()
        else:
            # construct a top-level StreamBlock from the list of block types
            self.stream_block = FeatureCustomizedStreamBlock(block_types, required=not self.blank)

        self.stream_block.set_meta_options(block_opts)
