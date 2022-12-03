# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)
# - Using string-based templates (instead of file-based templates)

import datetime
from flask import Flask, request, render_template_string, render_template
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///basic_app.sqlite'    # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'email@example.com'
    MAIL_PASSWORD = 'password'
    MAIL_DEFAULT_SENDER = '"MyApp" <noreply@example.com>'

    # Flask-User settings
    USER_APP_NAME = "Flask-User Basic App"      # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = True        # Enable email authentication
    USER_ENABLE_USERNAME = False    # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@example.com"


def create_app():
    """ Flask application factory """
    
    # Create Flask app load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Initialize Flask-BabelEx
    babel = Babel(app)

    # Initialize Flask-SQLAlchemy
    db = SQLAlchemy(app)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

        # User authentication information. The collation='NOCASE' is required
        # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
        email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
        email_confirmed_at = db.Column(db.DateTime())
        password = db.Column(db.String(255), nullable=False, server_default='')

        # User information
        first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

        # Define the relationship to Role via UserRoles
        roles = db.relationship('Role', secondary='user_roles')

    # Define the Role data-model
    class Role(db.Model):
        __tablename__ = 'roles'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(50), unique=True)

    # Define the UserRoles association table
    class UserRoles(db.Model):
        __tablename__ = 'user_roles'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
        role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    # Conversion to SQLAlchemy DB tables
    class Books(db.Model):
        __tablename__ = 'Books'
        id = db.Column(db.Integer(), primary_key=True)
        author = db.Column(db.String(50))
        title = db.Column(db.String(50), unique=True)
        description = db.Column(db.String(300))

    # Setup Flask-User and specify the User data-model
    user_manager = UserManager(app, db, User)

    # Create all database tables
    db.create_all()

    # Create 'member@example.com' user with no roles
    if not User.query.filter(User.email == 'member@example.com').first():
        user = User(
            email='member@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        db.session.add(user)
        db.session.commit()

    # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
    if not User.query.filter(User.email == 'admin@example.com').first():
        user = User(
            email='admin@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        user.roles.append(Role(name='Admin'))
        user.roles.append(Role(name='Agent'))
        db.session.add(user)
        db.session.commit()

    # The Home page is accessible to anyone
    @app.route('/')
    def home_page():
        return render_template("index.html")

    # The Admin page requires an 'Admin' role.
    @app.route('/admin')
    @roles_required('Admin')    # Use of @roles_required decorator
    def admin_page():
        return render_template('admin.html')
        
    @app.route("/contact")
    def contact_page():
        return render_template('contact.html')


    @app.route('/all_books')
    @login_required
    def all_books():
        # books = db.engine.execute('SELECT * FROM Book')
        # my_list_of_books = [row for row in books]
        # return render_template('all_books.html', books=my_list_of_books)
        if Books.__table__.exists(db.engine) :
            books = Books.query.all()
            books = Books.query.order_by(Books.id.desc())

            my_list_of_books = [row for row in books]

            return render_template('all_books.html', books=my_list_of_books)
        else:
            return render_template('all_books.html')

    @app.route('/edit/<id>', methods={'GET', 'POST'})
    @login_required
    def edit(id):

        book = Books.query.filter(Books.id == id).first()
        validation_error = ""
        
        if request.method == 'GET':
            request.form.author = book.author
            request.form.title = book.title
            request.form.description = book.description

        else:
            if Books.query.filter(Books.title == request.form['title']).first() is not None:
                validation_error = "Title already in use."
                return render_template('edit.html', validation_error=validation_error)
            else:
                book.author = request.form['author']
                book.title = request.form['title']
                book.description = request.form['description']

                db.session.add(book)
                db.session.commit()
                validation_error= book.title + " has been updated!"

        return render_template('edit.html', validation_error=validation_error)
    
    @app.route('/add_book', methods={'GET', 'POST'})
    @login_required
    def addbook():

        if not Books.__table__.exists(db.engine) :
            db.create_all()

        if request.method == 'POST':
            r_author = request.form['author']
            r_title = request.form['title']
            r_description = request.form['description']

            newbook = Books(author=r_author,title=r_title,description=r_description)
            db.session.add(newbook)
            db.session.commit()

            return render_template('index.html')
        return render_template('add_book.html', book_title="")

    @app.route('/seedDB')
    def seedDB():

        if not Books.__table__.exists(db.engine) :
            db.create_all()

        book1 = Books(author='Mary Shelley',title="Frankenstein",description="A horror story written by someone who could not scroll far enough to the right in the video for me to copy the full descriptions of each book")
        db.session.add(book1)

        book2 = Books(author='Henry James',title="The Turn of the Screw",description="Another Brick In The Wall by Pink Floyd is a good song")
        db.session.add(book2)

        book3 = Books(author='Max Weber',title="The Protestant Work Ethic and the Spirit: Stallion of the Cimarron",description="A blending of genres never before seen in fiction!")
        db.session.add(book3)

        book4 = Books(author='Robert Putnam',title="Bowling Alone",description="A classic late 2000s drama about the lead singer from Bowling For Soup, detailing his harrowing experience in solitary confinement.")
        db.session.add(book4)

        db.session.commit()
        
        message = "DB Seeded!"
        return render_template('index.html', message=message)

    @app.route("/eraseDB")
    def eraseDB():
        Books.__table__.drop(db.engine)
        return "<h1>DB Erased!</h1>"

    @app.context_processor
    def utility_processor():
        def isAdmin(user):
            sqlStatement = "SELECT roles.name FROM roles JOIN user_roles ON roles.id=user_roles.role_id JOIN users ON users.id=user_roles.user_id WHERE users.email='" + user + "' AND roles.name='Admin'"
            roleName = db.engine.execute(sqlStatement)
            roleName = [row for row in roleName]
            if len(roleName) > 0 and roleName[0]['name'] == 'Admin':
                returnValue = 1
            else:
                returnValue = 0
            return returnValue
        return dict(isAdmin=isAdmin)
    return app


# Start development web server
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)