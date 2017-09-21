(function($, window, document, undefined) {
  window.fixed_dimensions = function(prefix) {
    function disable_following_elems(target) {
      var height_li = target.closest("li").next("li");
      var width_li = height_li.next("li");
      height_li.find("input").prop("readonly", !target.prop("checked"));
      width_li.find("input").prop("readonly", !target.prop("checked"));
    }

    var target = $('#' + prefix + '-use');
    // Initialize existing elements to correct behavior state
    disable_following_elems(target);
    // Apply behavior to existing elements
    target.change(function() {
      disable_following_elems($(this));
    });

    function apply_disable_to_observer(mutations) {
      mutations.forEach(function (mutation) {
        var newNodes = mutation.addedNodes;
        if (newNodes != null) {
          $(newNodes).each(function() {
            target = $(this).find('.fieldname-use');
            if (target) {
              disable_following_elems(target);
              target.change(function() {
                disable_following_elems($(this));
              });
            }
          });
        }
      });
    }

    // Apply behavior to new elements
    var observer = new MutationObserver(apply_disable_to_observer);
    observer.observe(document, {childList: true, subtree: true, characterData: true});
  }
})(jQuery, this, this.document);
