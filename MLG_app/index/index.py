"""General page routes."""
from flask import Blueprint, render_template
from flask import current_app as app

# Blueprint Configuration
index_bp = Blueprint(
    'index_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

@index_bp.route('/', methods=['GET'])
def index():
    """Homepage."""
    return render_template(
        'index.html',
    )
