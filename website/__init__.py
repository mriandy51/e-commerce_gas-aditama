from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

import os

db = SQLAlchemy()
migrate = Migrate()
DB_NAME = 'database.sqlite3'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hbnwdvbn ajnbsjn ahe'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    migrate.init_app(app, db) 
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(id):
        from .models import User 
        return User.query.get(int(id))

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html')

    #  Blueprints
    from .views import views
    from .auth import auth
    from .admin import admin
    from .shop import shop
    from .info import info
    from .contact import contact
    from .report import report
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/')
    app.register_blueprint(shop, url_prefix='/')
    app.register_blueprint(info, url_prefix='/')
    app.register_blueprint(contact, url_prefix='/')
    app.register_blueprint(report, url_prefix='/')

    with app.app_context():
        
        create_database()
        create_gastruck()
        add_user()
        add_product()

    return app

def create_database():
    if not os.path.exists('instance/' + DB_NAME):
        db.create_all()
        print('Database Created')

def create_gastruck():
    from .models import GasTruck  
    if len(GasTruck.query.all()) < 1:
        new_gas_truck = GasTruck(delivery_status='Test', estimated_delivery='Test')
        db.session.add(new_gas_truck)
        db.session.commit()

def add_user():
    from .models import User 
    if len(User.query.all()) < 1:
        admin = [
            User(
                id=11111,
                email='full_admin@aditama.com',
                phone='08888640376',
                username='fulladmin',
                full_name='Full Admin',
                roles=1,
            ),
            User(
                id=22222,
                email='admin@aditama.com',
                phone='08879797842',
                username='admin',
                full_name='Admin',
                roles=2,
            ),
            User(
                id=33333,
                email='kasir@aditama.com',
                phone='081280641880',
                username='kasir',
                full_name='Kasir',
                roles=3,
            ),
            User(
                id=44444,
                email='staffgudang@aditama.com',
                phone='0889892382322',
                username='staffgudang',
                full_name='Staff Gudang',
                roles=4,
            ),
            User(
                id=55555,
                email='offline@aditama.com',
                phone='08111111111',
                username='offline_customer',
                full_name='Pelanggan Offline',
                roles=0,
            ),
        ]

        admin[0].password = '050611'
        admin[1].password = '050611'
        admin[2].password = '050611'
        admin[3].password = '050611'
        admin[4].password = '050611'

        try:
            db.session.bulk_save_objects(admin)
            db.session.commit()
            print('Admin User Successfully Added!')
        except Exception as err:
            print('Error: ', err)


def add_product():
    from .models import Product, ProductVariant
    if len(Product.query.all()) < 1:
        products = [
            {
                'name': 'Tabung Gas 3 kg',
                'picture': './media/tabung3kg.png',
                'variants': [
                    {
                        'name': 'Tabung Kosong Gas 3 kg',
                        'type': 'tabung_kosong',
                        'price': 182000,
                        'stock': 10
                    },
                    {
                        'name': 'Isi Gas 3 kg',
                        'type': 'refill',
                        'price': 18000,
                        'stock': 10
                    },
                    {
                        'name': 'Tabung Bocor Gas 3 kg',
                        'type': 'tabung_bocor',
                        'price': 0,
                        'stock': 0
                    }
                ]
            },
            {
                'name': 'Tabung Gas 5.5 kg',
                'picture': './media/tabung5_5kg.png',
                'variants': [
                    {
                        'name': 'Tabung Kosong Gas 5.5 kg',
                        'type': 'tabung_kosong',
                        'price': 190000,
                        'stock': 10
                    },
                    {
                        'name': 'Isi Gas 5.5 kg',
                        'type': 'refill',
                        'price': 95000,
                        'stock': 10
                    },
                    {
                        'name': 'Tabung Bocor Gas 5.5 kg',
                        'type': 'tabung_bocor',
                        'price': 0,
                        'stock': 0
                    }
                ]
            },
            {
                'name': 'Tabung Gas 12 kg',
                'picture': './media/tabung12kg.png',
                'variants': [
                    {
                        'name': 'Tabung Kosong Gas 12 kg',
                        'type': 'tabung_kosong',
                        'price': 400000,
                        'stock': 10
                    },
                    {
                        'name': 'Isi Gas 12 kg',
                        'type': 'refill',
                        'price': 195000,
                        'stock': 10
                    },
                    {
                        'name': 'Tabung Bocor Gas 12 kg',
                        'type': 'tabung_bocor',
                        'price': 0,
                        'stock': 0
                    }
                ]
            }
        ]

        try:
            for product_data in products:
                product = Product(
                    product_name=product_data['name'],
                    product_picture=product_data['picture']
                )
                db.session.add(product)
                db.session.flush() 

                for variant_data in product_data['variants']:
                    variant = ProductVariant(
                        product_id=product.id,
                        variant_name=variant_data['name'],
                        variant_type=variant_data['type'],
                        price=variant_data['price'],
                        stock=variant_data['stock']
                    )
                    db.session.add(variant)

            db.session.commit()
            print('Products Successfully Added!')
        except Exception as err:
            print('Error:', err)
            db.session.rollback()