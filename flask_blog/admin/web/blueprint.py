from flask import Blueprint

from flask_blog.admin.web import views

web = Blueprint("web", __name__)

# URL rules
web.add_url_rule("/", view_func=views.index, methods=["GET"])
web.add_url_rule("/login/", view_func=views.login, methods=["GET", "POST"])
web.add_url_rule("/logout/", view_func=views.logout, methods=["GET"])
web.add_url_rule("/categories/", view_func=views.blog_category_list, methods=["GET"])
web.add_url_rule("/categories/create/", view_func=views.blog_category_form, methods=["GET", "POST"])
web.add_url_rule(
    "/categories/<int:object_id>/", view_func=views.blog_category_form, methods=["GET", "POST"]
)
web.add_url_rule(
    "/categories/<int:object_id>/delete/",
    view_func=views.blog_category_delete,
    methods=["GET", "POST"],
)
web.add_url_rule("/posts/", view_func=views.blog_post_list, methods=["GET"])
web.add_url_rule("/posts/create/", view_func=views.blog_post_form, methods=["GET", "POST"])
web.add_url_rule("/posts/<int:object_id>/", view_func=views.blog_post_form, methods=["GET", "POST"])
web.add_url_rule(
    "/posts/<int:object_id>/delete/", view_func=views.blog_post_delete, methods=["GET", "POST"]
)
