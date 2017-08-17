(function ($, window, document, undefined) {
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
  $(window).load(function() {
    make_image_cards_same_height_in_same_row();
  });

}(jQuery, this, this.document));
