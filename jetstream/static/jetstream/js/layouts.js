(function ($, window, document, undefined) {

  /* This is the bit that enables raising and lowering of the description on
   * the image-panel-rollover.tpl */
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

  function make_image_cards_same_height_in_same_row() {
    var max_height = 0;
    $('.row').each(function() {
      $('.card.equal', this).each(function() {
        if ($(this).outerHeight(true) > max_height) {
          max_height = $(this).outerHeight(true);
        }
      });
      $('.card.equal', this).height(max_height);
    });
  }

  function set_up_video_blocks() {
    $('.video-block-overlay').on('click', function () {
      // Hide the overlay to remove the title set in the VideoBlock.
      $(this).hide();

      var $iframe = $('iframe', $(this).parent());
      var iframe = $iframe[0];
      // YouTube and Vimeo videos require different actions to make this work.
      if ($iframe.data('provider') == 'YouTube') {
        iframe.src = iframe.src.replace('showinfo=0', 'showinfo=0&autoplay=1');
      }
      else if ($iframe.data('provider') == 'Vimeo') {
        iframe.src = iframe.src.replace('portrait=0', 'portrait=0&autoplay=1');
      }
    });
  }

  $(document).ready(function() {
    set_up_image_animations();
    set_up_video_blocks();
  });
  $(window).load(function() {
    make_image_cards_same_height_in_same_row();
  });

}(jQuery, this, this.document));
