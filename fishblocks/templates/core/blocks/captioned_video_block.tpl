<div class="captioned-video-block">
  <div class="embedded-video">{{ video | safe }}</div>
  <p class="caption">{{ caption }}</p>
  {% if credit %}
  <p class="photo-credit">{{ credit }}</p>
  {% endif %}
</div>
