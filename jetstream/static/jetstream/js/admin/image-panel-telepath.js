class ImagePanelBlockDefinition extends window.wagtailStreamField.blocks.StructBlockDefinition {
  /**
   * This function gets called by wagtail's StreamField javascript each time a new ImagePanelBlock is generated
   * within the form. The 'prefix' argument is a string that uniquely identifies the instance of the
   * ImagePanelBlock that was just generated.
   */
  render(placeholder, prefix, initialState, initialError) {
    // 1. Render the block. This needs to happen before the extra behavior is added, because otherwise there will be
    // nothing to attach that behavior to.
    const block = super.render(placeholder, prefix, initialState, initialError);

    // 2. Set up extra behavior.
    var field = null, field_sibling = null;

    /**
     * Sets up the Display Caption checkbox to only appear when an appropriate Style is selected.
     */
    function configure_display_caption_checkbox(prefix, current_style) {
      var checkbox = $(`#${prefix}-display_caption`);
      // If the Style dropdown is set to a style where optionally displaying the caption doesn't make sense, don't
      // show the Display Caption field.
      if (['rollover', 'hero', 'captioned', 'link'].indexOf(current_style) > -1) {
        // If there's no checkbox, we've already stored and removed the field, so we can't do it again.
        if (!checkbox.length) {
          return;
        }
        // If we use .show()/.hide(), the alternating striping for the fields won't update, which looks ugly.
        // This method actually removes the Display Caption field from the DOM while an inappropriate Style is set.
        // This is safe while submitting because a missing checkbox isn't sent as POST data anyway, meaning Django
        // will treat the value as False.
        // 2021-04-28 rrollins: NOTE, the reasoning for this is currently moot, as fields no longer have alternating
        // striping. We might add it in the future, though, so I'm leaving this as-is.
        field = checkbox.closest('.field').parent();
        field_sibling = field.prev();
        field.detach();
      }
      else if (field) {
        field_sibling.after(field);
        field = null;
        field_sibling = null;
      }
    }

    // Get the "Style" dropdown for this instance of ImagePanelBlock.
    var style_select = $(`#${prefix}-style`);
    // Initialize the Display Caption checkbox appropriately.
    configure_display_caption_checkbox(prefix, style_select.val());
    // Re-toggle the Display Caption checkbox each time the Style is changed.
    style_select.change(function() {
      configure_display_caption_checkbox(prefix, $(this).val());
    });

    // 3. Return the block that was rendered at the top of this function.
    return block;
  }
}
// This connects the above javascript to the Python Adapter code: js_constructor = 'jetstream.ImagePanelBlock'
window.telepath.register('jetstream.ImagePanelBlock', ImagePanelBlockDefinition);
