(function ($, window, document) {
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
    set_up_video_blocks();
  });
  $(window).load(function() {
    make_image_cards_same_height_in_same_row();
  });
}(jQuery, this, this.document));
