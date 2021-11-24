{% load jetstream_tags %}

{% image_dimensions self.fixed_dimensions parent_width parent_height 1350 759 as dimensions %}
<div class="video-block"
  {% if not parent_height %}
    {% if self.fixed_dimensions.use %}
      style="max-width: {{ self.fixed_dimensions.width}}px; max-height: {{ self.fixed_dimensions.height}}px;"
    {% else %}
      style="max-width: 600px; max-height: 400px;"
    {% endif %}
  {% else %}
    style="max-height: {{ parent_height }}px;"
  {% endif %}
>
  {% responsive_video self.video.url dimensions.width extra_classes="video-block__video" %}
  <div class="video-block__overlay">
    {% if self.title %}
      <div class="video-block__title-banner">
        <div class="video-block__title">{{ self.title }}</div>
      </div>
    {% endif %}
  </div>
</div>
