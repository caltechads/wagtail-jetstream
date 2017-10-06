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
    if (!Modernizr.mobile) {
      // The .video-block-overlay div covers the entire video block. On desktop, we need to translate clicks through
      // it and onto the iframe.
      $('.video-block-overlay').on('click', function() {
        // Hide the overlay so that video's controls are fully accessible.
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
    else {
      // On mobile, we set up the overlay to be untouchable; clicks will pass through it and hit the iframe directly.
      // This doesn't hide the title, but that's OK on phones because the video plays in full screen.
      $('.video-block-overlay').addClass('mc-hammer');
    }

    // Rergardless of whether we're on mobile, make clicks/taps on the title itself hide the overlay.
    // This lets tablet users hide the title with a second click.
    $('.video-block-title-background').on('click', function() {
      $(this).parent().hide();
    });
  }

  $(document).ready(function() {
    set_up_video_blocks();
  });

  $(window).load(function() {
    make_image_cards_same_height_in_same_row();
  });
}(jQuery, this, this.document));
