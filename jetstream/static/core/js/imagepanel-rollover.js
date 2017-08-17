(function ($, window, document, undefined) {
  function set_up_image_animations() {
    $('.image-block-link .entry').each(function(ndx,entry) {

      var closetimer = null, hovertimer = null;

      function slide_up() {
        $('.text', $(entry)).animate({'top': '0'});
      }

      function slide_down() {
        // NOTE: If the "top" property of ".image-gallery .text" changes in the CSS, this also has to change!
        $('.text', $(entry)).animate({'top': '70%'});
      }

      // Open the specified entry after half a second.
      function start_opentimer() {
        cancel_opentimer();
        hovertimer = _.delay(slide_up, 500);
      }

      // Prevent the next branch-open from occuring.
      function cancel_opentimer() {
        clearTimeout(hovertimer);
      }

      // Close all branches after half a second.
      function start_closetimer() {
        cancel_closetimer();
        cancel_opentimer();
        closetimer = _.delay(slide_down, 500);
      }

      // Prevent the next menu-close from occuring.
      function cancel_closetimer() {
        clearTimeout(closetimer);
      }

      // Don't implement the hover functionality on mobile devices. Tapping a entry should simply click the link.
      if (!$('html').hasClass('touch')) {
        $(entry).hover(start_opentimer, start_closetimer);
        $(entry).hover(cancel_closetimer, start_closetimer);
      }
    });
  }
  $(document).ready(function() {
    set_up_image_animations();
  });

}(jQuery, this, this.document));
