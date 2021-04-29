class DimensionsOptionsBlockDefinition extends window.wagtailStreamField.blocks.StructBlockDefinition {
  /**
   * This function gets called by wagtail's StreamField javascript each time a new DimensionsOptionsBlock is generated
   * within the form. The 'prefix' argument is a string that uniquely identifies the instance of the
   * DimensionsOptionsBlock that was just generated.
   */
  render(placeholder, prefix, initialState, initialError) {
    // 1. Render the block. This needs to happen before the extra behavior is added, because otherwise there will be
    // nothing to attach that behavior to.
    const block = super.render(placeholder, prefix, initialState, initialError);

    // 2. Set up extra behavior.
    function toggle_height_and_width_editability(target) {
      // To get at the Height and Width fields, we traverse up the DOM to the .struct-block object that parents
      // this entire block.
      var parent_ul = target.closest('.struct-block');
      // On each number input within this DimensionsOptionsBlock, set the readOnly property to True when the "Use"
      // checkbox is unchecked, and False when it's checked. Since the checkbox defaults to unchecked, these properties
      // are not editable by default.
      parent_ul.find('input[type="number"]').prop('readOnly', !target.prop('checked'));
    }

    // Get the "Use Fixed Dimensions" checkbox for this instance of the DimensionsOptionsBlock.
    var target = $('#' + prefix + '-use');
    // Initialize existing elements to correct editability state.
    toggle_height_and_width_editability(target);
    // Re-toggle editability each time the checkbox is clicked.
    target.change(function() {
      toggle_height_and_width_editability($(this));
    });

    // 3. Return the block that was rendered at the top of this function.
    return block;
  }
}
// This connects the above javascript to the Python Adapter code: js_constructor = 'jetstream.DimensionsOptionsBlock'
window.telepath.register('jetstream.DimensionsOptionsBlock', DimensionsOptionsBlockDefinition);
