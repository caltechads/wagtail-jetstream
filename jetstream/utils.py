def get_block_tuple(block_inst):
    """
    Returns the canned block tuple for use in StreamField and StreamBlock definitions (but NOT in StructBlocks!).
    We use this everywhere so that our code consistently generates the same tuple at every organiziational level.
    """
    try:
        return block_inst.get_block_tuple()
    except AttributeError:
        # If the block instance hasn't got a get_block_tuple() method, build the default tuple.
        return (block_inst.__class__.__name__, block_inst)


class BlockTupleMixin(object):
    """
    All our custom block classes need to mixin this class so that our code consistently generates the same tuple at
    every organiziational level (e.g. the Page.body level and the TwoColumnBlock level).

    Classes that need to use a custom string for their block tuple (e.g. TwoColumnBlock and BaseTwoColumnSubblock, which
    both need the same tuple) can override get_block_tuple().
    """

    @classmethod
    def get_block_machine_name(cls):
        return cls.__name__

    def get_block_tuple(self):
        return (self.__class__.__name__, self)


# Used for the "choices" param on StreamField blocks that can list a variable
# number of items
SHOW_CHOICES = [
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
    (6, 6),
    (7, 7),
    (10, 10),
    (15, 15),
    (20, 20),
    (25, 25),
]

BACKGROUND_COLORS = [
    (None,  'Transparent'),
    ('white', 'White'),
    ('black', 'Black'),
    ('orange', 'Orange'),
    ('ltgray', 'Light Gray'),
    ('midgray', 'Mid Gray'),
    ('darkergray', 'Dark Gray'),
    ('dkgray', 'Very Dark Gray'),
    ('olivegreen', 'Olive Green'),
    ('purple', 'Purple'),
    ('darkteal', 'Dark Teal'),
]

FOREGROUND_COLORS = [
    (None, 'Default'),
    ('dkgray', 'Dark Gray'),
    ('black', 'Black'),
    ('white', 'White')
]
