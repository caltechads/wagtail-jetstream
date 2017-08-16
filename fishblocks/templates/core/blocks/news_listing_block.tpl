{% load static core_tags wagtailcore_tags wagtailimages_tags bleach_tags %}

<div class="news-listing-block
     {% if self.color.text_color %} text-color-{{ self.color.text_color }}{% endif %}
     {% if self.color.background_color and not self.color.background_image %} bg-color bg-color-{{ self.color.background_color }}{% endif %}
     {% if self.fixed_dimensions %} fixed{% endif %}
"
     {% if self.fixed_dimensions.use %}
     style="height: {{ self.fixed_dimensions.height }}px; width: {{ self.fixed_dimensions.width }}px"
     {% endif %}
>
  {% if self.title %}
    <h3 class="block-title">{{ self.title }}</h3>
  {% endif %}

  {% retrieve_news request self.show as articles %}
  {% if articles %}
    {% for article in articles %}
      <div class="news-mini-teaser">
        <div class="publish-date">
          {{ article.first_published_at | date:'m/d/Y' }}
        </div>
        <h4 class="title">
          <a href="{% pageurl article %}">{{ article.listing_title | default:article.title | bleach }}</a>
        </h4>
      </div>
    {% endfor %}
    <a class="rss-link" href="{% news_feed_url %}">
      <img src="{% static 'theme/images/feed.png' %}"> Subscribe via RSS
    </a>
  {% else %}
    <h4>Sorry, we have no News at this time.</h4>
  {% endif %}
  {% if self.color.background_image %}
    {% image self.color.background_image fill-800x600 as bg_image %}
    <img class="background-image" src="{{ bg_image.url }}">
  {% endif %}
</div>
