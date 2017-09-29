{% load jetstream_tags %}

<div class="video-block"
  {% if not parent_height %}
    {% if self.fixed_dimensions.use %}
      style="width: {{ self.fixed_dimensions.width}}px; height: {{ self.fixed_dimensions.height}}px;"
    {% else %}
      style="width: 600px; height: 400px;"
    {% endif %}
  {% else %}
    style="height: {{ parent_height }}px;"
  {% endif %}
>
  {% if self.fixed_dimensions.use %}
    {% arbitrary_video self.video self.fixed_dimensions.width self.fixed_dimensions.height %}
  {% else %}
    {% if parent_width %}
      {% arbitrary_video self.video parent_width parent_height %}
    {% else %}
      {% arbitrary_video self.video 600 400 %}
    {% endif %}
  {% endif %}
  <div class="video-block-overlay">
    {% if self.title %}
      <div class="video-block-title-background">
        <div class="video-block-title">{{ self.title }}</div>
      </div>
    {% endif %}
  </div>
</div>
