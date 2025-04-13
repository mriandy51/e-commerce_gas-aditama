from flask import Blueprint, render_template, request, send_from_directory
from .models import GasTruck, Product
from . import db

info = Blueprint('info', __name__)

@info.route('/info')
def infos():
    # Get produk aktif and ASC 
    products = Product.query.filter_by(is_active=True).order_by(Product.id.asc()).all()
    
    # Filter produk with at least 1 varian aktif
    products = [p for p in products if any(v.is_active for v in p.variants)]
    
    gasitems = GasTruck.query.order_by(GasTruck.id.desc()).limit(1)
    
    product_info = []
    for product in products:
        variants_info = []
        for variant in product.variants:
            if variant.is_active and variant.variant_type != 'tabung_bocor': #Varian aktif & !=tbg drop
                variants_info.append({
                    'name': variant.variant_name,
                    'price': variant.price,
                    'stock': variant.stock
                })
        
        product_info.append({
            'name': product.product_name,
            'picture': product.product_picture,
            'variants': variants_info,
            'date_added': product.date_added
        })

    return render_template('info.html', products=product_info, gasitems=gasitems)


@info.route("/OneSignalSDKWorker.js")
@info.route("/OneSignalSDKUpdaterWorker.js")
def onesignal_service_worker():
    """Serve OneSignal Service Worker files."""
    return send_from_directory('static', request.path[1:], mimetype="application/javascript")