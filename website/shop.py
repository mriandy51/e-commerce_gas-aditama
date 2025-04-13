from flask import Blueprint, render_template
from .models import Product, Cart
from flask_login import current_user

shop = Blueprint('shop', __name__)


@shop.route('/shop')
def shops():
    products = Product.query.filter_by(is_active=True)\
        .order_by(Product.date_added).all()
        
    # Get atleast 1 variant aktif only
    
    return render_template('shop.html', 
                         products=products,
                         cart=Cart.query.filter_by(customer_link=current_user.id).all() if current_user.is_authenticated else [])