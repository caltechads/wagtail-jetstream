(function ($, window, document, undefined) {
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
}(jQuery, this, this.document));
