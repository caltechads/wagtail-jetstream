(function($, window, document, undefined) {
  /**
   * This function gets called by wagtail's StreamField javascript each time a new ImagePanelBlock is generated
   * within the form. The 'prefix' argument is a string that uniquely identifies the ImagePanelBlock instance.
   */
  window.image_panel = function(prefix) {
    var stored_li = null, stored_li_sibling = null;

    /**
     * Sets up the Display Caption checkbox to only appear when an appropriate Style is selected.
     */
    function configure_display_caption_checkbox(prefix, current_style) {
      var checkbox = $('#' + prefix + '-display_caption');
      // If the Style dropdown is set to a style where optionally displaying the caption doesn't make sense, don't
      // show the Display Caption field.
      if (['rollover', 'hero', 'captioned', 'link'].indexOf(current_style) > -1) {
        // If there's no checkbox, we've already stored and removed the field, so we can't do it again.
        if (!checkbox.length) {
          return;
        }
        // If we use .show()/.hide(), the striping for the <li>s in the form won't update, which looks ugly.
        // This method actually removes the Display Caption field from the DOM while an inappropriate Style is set.
        // This is safe while submitting because a missing checkbox isn't sent as POST data anyway, meaning Django
        // will treat the value as False.
        stored_li = checkbox.closest('li');
        stored_li_sibling = stored_li.prev();
        stored_li.detach();
      }
      else if (stored_li) {
        stored_li_sibling.after(stored_li);
        stored_li = null;
        stored_li_sibling = null;
      }
    }

    // Get the "Style" dropdown for this instance of ImagePanelBlock.
    var style_select = $('#' + prefix + '-style');
    // Initialize the Display Caption checkbox appropriately.
    configure_display_caption_checkbox(prefix, style_select.val());
    // Re-toggle the Display Caption checkbox each time the Style is changed.
    style_select.change(function() {
      configure_display_caption_checkbox(prefix, $(this).val());
    });
  }
})(jQuery, this, this.document);
