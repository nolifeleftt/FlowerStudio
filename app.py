from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    isActive = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'description': self.description,
            'image': self.image,
        }


@app.route('/cart/reset_quantity', methods=['POST'])
def reset_cart_quantity():
    Cart.query.update({Cart.quantity: 0})
    db.session.commit()
    return redirect('/cart')


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    def total_price(self):
        return Item.query.get(self.item_id).price * self.quantity

    @classmethod
    def decrease_quantity(cls, item_id):
        cart_item = cls.query.filter_by(item_id=item_id).first()
        if cart_item and cart_item.quantity > 1:
            cart_item.quantity -= 1
            db.session.commit()
        elif cart_item and cart_item.quantity == 1:
            db.session.delete(cart_item)
            db.session.commit()

    @classmethod
    def increase_quantity(cls, item_id):
        cart_item = cls.query.filter_by(item_id=item_id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = cls(item_id=item_id)
            db.session.add(cart_item)
        db.session.commit()
@app.route('/')
def index():
    items = Item.query.order_by(Item.price).all()
    return render_template('index.html', data=items)

@app.route('/create', methods=['POST', 'GET'])
def create():
    if request.method == "POST":
        title = request.form['title']
        price = request.form['price']
        description = request.form['description']
        image = request.form['image']
        item = Item(title=title, price=price, description=description, image=image)

        try:
            db.session.add(item)
            db.session.commit()
            return redirect('/')
        except:
            return "Error"
    else:
        items = Item.query.all()
        return render_template('create.html', items=items)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    print(session)
    if request.method == 'POST':
        item = Item.query.filter_by(id=item_id).first()
        if item:
            cart_item = Cart.query.filter_by(item_id=item.id).first()
            if cart_item:
                cart_item.quantity += 1
            else:
                cart_item = Cart(item_id=item.id)
                db.session.add(cart_item)
            db.session.commit()
            flash('Товар добавлен в корзину')
            # Добавление item_id в список в сессии
            session.setdefault('cart', []).append(item_id)
            return redirect('/')
        else:
            flash('Товар не найден')
            return redirect('/')
    else:
        return redirect('/')

@app.route('/cart/decrease_quantity/<item_id>', methods=['POST'])
def decrease_quantity(item_id):
    Cart.decrease_quantity(item_id)
    return redirect(url_for('cart'))


@app.route('/cart/increase_quantity/<item_id>', methods=['POST'])
def increase_quantity(item_id):
    Cart.increase_quantity(item_id)
    return redirect(url_for('cart'))

@app.route('/delete_all_items', methods=['GET', 'POST'])
def delete_all_items():
    db.session.query(Item).delete()
    db.session.commit()
    return redirect('/create')

@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    item = Item.query.filter_by(id=item_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Товар удален успешно!', 'success')
    else:
        flash('Товар не найден', 'error')
    return redirect(url_for('create'))
@app.route('/cart')
def cart():
    cart_items = []
    for item_id in session.get('cart', []):
        item = Item.query.get(item_id)
        if item:
            cart_item = Cart.query.filter_by(item_id=item.id).first()
            if cart_item and cart_item.item_id not in [i['id'] for i in cart_items]:
                cart_items.append({
                    'id': item.id,
                    'title': item.title,
                    'price': item.price,
                    'quantity': cart_item.quantity,
                    'image': item.image,
                })
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', data=cart_items, total=total)

@app.route('/deactivate/<int:item_id>', methods=['POST'])
def deactivate(item_id):
    item = Item.query.get_or_404(item_id)
    item.isActive = False

    try:
        db.session.commit()
        return redirect('/create')
    except:
        return 'Error'

@app.route('/activate/<int:item_id>', methods=['POST'])
def activate(item_id):
    item = Item.query.get_or_404(item_id)
    item.isActive = True

    try:
        db.session.commit()
        return redirect('/create')
    except:
        return 'Error'


@app.route('/cart/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    # Получаем текущую корзину из сессии
    cart = session.get('cart', [])

    # Если товар найден в корзине, удаляем его
    if item_id in cart:
        cart.remove(item_id)

        # Получаем информацию о товаре из базы данных
        item = Item.query.get(item_id)

        # Если товар найден, уменьшаем его количество в корзине на 1
        if item:
            cart_item = Cart.query.filter_by(item_id=item_id).first()
            if cart_item:
                cart_item.quantity -= 1
                db.session.commit()

        session['cart'] = cart
        flash('Товар успешно удален из корзины')
    else:
        flash('Товар не найден в корзине')

    return redirect('/cart')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
