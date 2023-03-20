from flask import Blueprint

from flask_blog.admin.api import views

api = Blueprint("api", __name__)

# URL rules
api.add_url_rule("/order-categories/", view_func=views.order_blog_categories, methods=["POST"])
api.add_url_rule("/render-markdown/", view_func=views.render_html, methods=["POST"])
api.add_url_rule("/upload-image/", view_func=views.upload_image, methods=["GET", "POST"])
