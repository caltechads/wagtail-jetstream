{% load static jetstream_tags %}

<script defer src="{% static 'jetstream/js/video-block.js' %}"></script>

<div class="video-block"
  {% if not parent_height or self.fixed_dimensions.use %}
    {% comment %}
      If this gets rendered outside of a parent block, or fixed_dimentions is enabled, we need to follow the width and
      height set on the block. Otherwise the div will stretch to fill the page.
    {% endcomment %}
    style="width: {{ self.fixed_dimensions.width }}px; height: {{ self.fixed_dimensions.height }}px;"
  {% else %}
    style="height: {{ parent_height }}px;"
  {% endif %}
>
  {% if parent_width and not self.fixed_dimensions.use %}
    {% arbitrary_video self.video parent_width parent_height %}
  {% else %}
    {% arbitrary_video self.video self.fixed_dimensions.width self.fixed_dimensions.height %}
  {% endif %}
  <div class="video-block-overlay">
    {% if self.title %}
      <div class="video-block-title-background">
        <div class="video-block-title">{{ self.title }}</div>
      </div>
    {% endif %}
  </div>
</div>
