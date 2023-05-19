from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')

db = SQLAlchemy(app)
ma = Marshmallow(app)
bc = Bcrypt(app)


class User(db.Model):
    id = db.Column (db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String, nullable=False)
    blog_user = db.relationship("Blog", backref="user", cascade="all, delete, delete-orphan")

    def __init__(self, email, password):
        self.email = email
        self.password = password
        

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    date = db.Column(db.String, nullable=False)
    blog_title = db.Column(db.String, nullable=False, unique=True)
    text_field = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String, unique=True)
    published = db.Column(db.String, nullable=False)
    fix_it_fred = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, id, date, blog_title, text_field, image_url, published, fix_it_fred ):
        self.id = id
        self.date = date
        self.blog_title = blog_title
        self.text_field = text_field
        self.image_url = image_url
        self.published = published
        self.fix_it_fred = fix_it_fred



class BlogSchema(ma.Schema):
    class Meta:
        fields = ('id', 'date', 'blog_title', 'text_field', 'image_url', 'published', 'fix_it_fred')

blog_schema = BlogSchema()
multi_blog_schema = BlogSchema(many=True)

        
class UserSchema(ma.Schema):
    blog_user = ma.Nested(multi_blog_schema)
    class Meta:
        fields = ('id', 'email', 'password', 'blog_user')

user_schema = UserSchema()
multi_user_schema = UserSchema(many=True)



@app.route('/user/create', methods=["POST"])
def create_account():
    if request.content_type != 'application/json':
        return jsonify("Error: JSONIFY")
    
    post_data = request.get_json()
    email = post_data.get("email")
    password = post_data.get("password")

    pw_hash = bc.generate_password_hash(password, 15).decode("utf-8")

    new_user = User(email, pw_hash)
    db.session.add(new_user)
    db.session.commit()


    return jsonify("User Created!", user_schema.dump(new_user))


@app.route("/verify", methods=["POST"])
def verify():
    if request.content_type != "application/json":
        return jsonify("Error: Data format submit incorrect")
    post_data = request.get_json()
    email = post_data.get("email")
    password = post_data.get("password")

    user = db.session.query(User).filter(User.email == email).first()

    if user is None:
        return jsonify("User cannot be verified!")
    if not bc.check_password_hash(user.password, password):
        return jsonify("User cannot be verified!")
    if user.email != "kressercolton12@gmail.com":
        return jsonify("AH AH AH! You didn't say the magic word!")
    
    return jsonify("User said the magic word!")


@app.route('/user/get')
def get_user():
    users = db.session.query(User).all()
    return jsonify(multi_user_schema.dump(users))


@app.route('/user/delete/<id>', methods=["DELETE"])
def delete_user(id):
    delete_user = db.session.query(User).filter(User.id == id).first()
    db.session.delete(delete_user)
    db.session.commit()
    return jsonify("User was deleted!")



@app.route('/user/update/<id>', methods=["PUT"])
def udate_user(id):
    if request.content_type != 'application/json':
        return jsonify("Input must be JSON!")
    put_data = request.get_json()
    email = put_data.get('email')
    edit_user = db.session.query(User).filter(User.id == id).first()

    if email != None:
        edit_user.email = email

    db.session.commit()
    return jsonify("User Info Updated!")


@app.route('/user/editpassword/<id>', methods=["PUT"])
def edit_password(id):
    if request.content_type != 'application/json':
        return jsonify("Error: Cannot update password!")
    password = request.get_json().get("password")
    user = db.session.query(User).filter(User.id == id).first()
    pw_hash = bc.generate_password_hash(password, 15).decode('utf-8')
    user.password = pw_hash

    db.session.commit()

    return jsonify("Password has been changed!", user_schema.dump(user))


@app.route('/blog/get/published')
def get_all_blogs(published):
    gab = db.session.query(Blog).filter(Blog.published == published).all()
    return jsonify(multi_blog_schema.dump(gab))


@app.route('/blog/create', methods=["POST"])
def create_blog():
    if request.content_type != 'application/json':
        return jsonify("Unable to create new Blog, try again!")
    
    post_data = request.get_json()
    date = post_data.get ("date")
    blog_title = post_data.get ("blog_title")
    text_field = post_data.get ("text_field")
    image_url = post_data.get ("image_url")
    published = post_data.get("published")
    fix_it_fred = post_data.get ("fix_it_fred")

    existing_blog_check = db.session.query(Blog).filter(Blog.blog_title == blog_title).first()
    if existing_blog_check is not None:
        return jsonify("Blog title is already being used, try again!")
    
    new_blog = Blog(date, blog_title, text_field, image_url, published, fix_it_fred)
    db.session.add(new_blog)
    db.session.commit()

    return jsonify(blog_schema.dump(new_blog))


@app.route('/blog/update/<id>', methods=["PUT"])
def ub(id):
    if request.content_type != "application/json":
        return jsonify("Cannot update blog, try again!")
    put_data = request.get_json()
    text_field = put_data('text')
    blog_title = put_data('blog_title')
    image_url = put_data('image_url')

    update_blog = db.session.query(Blog).filter(Blog.id == id).first()
    update_blog.text_field = text_field
    update_blog.blog_title = blog_title
    update_blog.image_url = image_url
    db.session.commit()

    return jsonify(blog_schema.dump(blog))


@app.route('/blog/delete/<id>', methods=["DELETE"])
def removeblog(id):
    blog = db.session.query(Blog).filter(Blog.id == id).first()
    db.session.delete(blog)
    db.session.commit()

    return jsonify("Blog Post has been DELETED!", blog_schema.dump(blog))



if __name__ == "__main__":
    app.run(debug = True)
