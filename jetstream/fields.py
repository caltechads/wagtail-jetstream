from wagtail.wagtailcore.blocks import Block
from wagtail.wagtailcore.fields import StreamField

from jetstream.blocks import FeatureCustomizedStreamBlock


class FeatureCustomizedStreamField(StreamField):

    def __init__(self, block_types, **kwargs):
        super(StreamField, self).__init__(**kwargs)
        if isinstance(block_types, Block):
            self.stream_block = block_types
        elif isinstance(block_types, type):
            self.stream_block = block_types(required=not self.blank)
        else:
            self.stream_block = FeatureCustomizedStreamBlock(block_types, required=not self.blank)
