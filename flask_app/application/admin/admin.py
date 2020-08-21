"""General page routes."""
from flask import Blueprint, render_template, g
from flask import current_app as app

# Blueprint Configuration
admin_bp = Blueprint(
    'admin_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/admin/static/'
)

@admin_bp.route('/devnotes', methods=['GET'])
def devnotes():
    return render_template(
        'devnotes.html',
    )