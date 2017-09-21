(function($, window, document, undefined) {
  /**
   * This function gets called by wagtail's StreamField javascript each time a new DimensionsOptionsBlock is generated
   * within the form. The 'prefix' argument is a string that uniquely identifies the instance of the
   * DimentionsOptionsBlock that was just generated.
   */
  window.fixed_dimensions = function(prefix) {
    function toggle_height_and_width_editability(target) {
      // To get at the Height and Width fields, we traverse up the tree to the closest <ul>, which is the nearest
      // ancestor of both this checkbox and the height/width inputs.
      var parent_ul = target.closest('ul');
      // On each number input within this DimentionsOptionsBlock, set the readOnly property to True when the "Use"
      // checkbox is unchecked, and False when it's checked. Since the checkbox defaults to unchecked, these properties
      // are not editable by default.
      parent_ul.find('input[type="number"]').prop('readOnly', !target.prop('checked'));
    }

    // Get the "Use Fixed Dimentions" checkbox for this instance of the DimentionsOptionsBlock.
    var target = $('#' + prefix + '-use');
    // Initialize existing elements to correct editability state.
    toggle_height_and_width_editability(target);
    // Re-toggle editability each time the checkbox is clicked.
    target.change(function() {
      toggle_height_and_width_editability($(this));
    });
  }
})(jQuery, this, this.document);
