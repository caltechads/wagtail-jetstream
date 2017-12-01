(function($, window, document, undefined) {
  /**
   * This function gets called by wagtail's StreamField javascript each time a new ImageGalleryBlock is generated
   * within the form. The 'prefix' argument is a string that uniquely identifies the ImageGalleryBlock instance.
   */
  window.image_gallery = function(prefix) {
    var stored_li = null, stored_li_sibling = null;

    /**
     * Sets up the Columns field to only appear when an appropriate Style is selected.
     */
    function configure_columns_dropdown(prefix, current_style) {
      var columns_dropdown = $('#' + prefix + '-columns');
      // If the Style dropdown is set to a style with columns (e.g. gallery), show the Columns field.
      if (current_style != 'gallery') {
        // If there's no dropdown, we've already stored and removed the field, so we can't do it again.
        if (!columns_dropdown.length) {
          return;
        }
        // If we use .show()/.hide(), the striping for the <li>s in the form won't update, which looks ugly.
        // Thus, we convert the dropdown into a hidden input with the same value.
        var parent_block = columns_dropdown.closest('.sequence-member');
        var hidden_id = prefix + '-columns-hidden';
        var hidden_name = columns_dropdown.attr('name');
        var hidden_value = columns_dropdown.val();
        parent_block.append(
          $('<input type="hidden" id="' + hidden_id + '" name="' + hidden_name + '" value="' + hidden_value + '">')
        );
        stored_li = columns_dropdown.closest('li');
        stored_li_sibling = stored_li.prev();
        stored_li.detach();
      }
      else if (stored_li) {
        stored_li_sibling.after(stored_li);
        stored_li = null;
        stored_li_sibling = null;
        $('#' + prefix + '-columns-hidden').remove();
      }
    }

    // Get the "Style" dropdown for this instance of ImagePanelBlock.
    var style_select = $('#' + prefix + '-style');
    // Initialize the Columns dropdown appropriately.
    configure_columns_dropdown(prefix, style_select.val());
    // Re-toggle the Columns dropdown each time the Style is changed.
    style_select.change(function() {
      configure_columns_dropdown(prefix, $(this).val());
    });
  }
})(jQuery, this, this.document);
