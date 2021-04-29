class ImageGalleryBlockDefinition extends window.wagtailStreamField.blocks.StructBlockDefinition {
  /**
   * This function gets called by wagtail's StreamField javascript each time a new ImageGalleryBlock is generated
   * within the form. The 'prefix' argument is a string that uniquely identifies the instance of the
   * ImageGalleryBlock that was just generated.
   */
  render(placeholder, prefix, initialState, initialError) {
    // 1. Render the block. This needs to happen before the extra behavior is added, because otherwise there will be
    // nothing to attach that behavior to.
    const block = super.render(placeholder, prefix, initialState, initialError);

    // 2. Set up extra behavior.
    var field = null, field_sibling = null;

    /**
     * Sets up the Columns field to only appear when an appropriate Style is selected.
     */
    function configure_columns_dropdown(current_style) {
      var columns_dropdown = jQuery(`#${prefix}-columns`);
      // If the Style dropdown is set to a style with columns (e.g. gallery), show the Columns field.
      if (current_style != 'gallery') {
        // If there's no dropdown, we've already stored and removed the field, so we can't do it again.
        if (!columns_dropdown.length) {
          return;
        }
        // If we use .show()/.hide(), the striping for the fields in the form won't update, which looks ugly.
        // Thus, we convert the dropdown into a hidden input with the same value.
        var parent_block = columns_dropdown.closest('.struct-block');
        var hidden_id = prefix + '-columns-hidden';
        var hidden_name = columns_dropdown.attr('name');
        var hidden_value = columns_dropdown.val();
        parent_block.append(
          jQuery('<input type="hidden" id="' + hidden_id + '" name="' + hidden_name + '" value="' + hidden_value + '">')
        );
        field = columns_dropdown.closest('.field').parent();
        field_sibling = field.prev();
        field.detach();
      }
      else if (field) {
        field_sibling.after(field);
        field = null;
        field_sibling = null;
        jQuery(`#${prefix}-columns-hidden`).remove();
      }
    }

    // Get the "Style" dropdown for this instance of ImagePanelBlock.
    var style_select = jQuery(`#${prefix}-style`);
    // Initialize the Columns dropdown appropriately.
    configure_columns_dropdown(style_select.val());
    // Re-toggle the Columns dropdown each time the Style is changed.
    style_select.change(function() {
      configure_columns_dropdown(jQuery(this).val());
    });

    // 3. Return the block that was rendered at the top of this function.
    return block;
  }
}
// This connects the above javascript to the Python Adapter code: js_constructor = 'jetstream.ImageGalleryBlock'
window.telepath.register('jetstream.ImageGalleryBlock', ImageGalleryBlockDefinition);
