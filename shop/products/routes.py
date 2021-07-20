import re

import flask_login
from flask import redirect, request, render_template, url_for, flash, session, current_app
from flask_login import current_user
from keras.datasets import imdb

from shop import db, app, photos
from .forms import Addproduct

from keras.preprocessing import sequence
import numpy as np

import secrets, os
from .models import Brand, Category, AddProduct, ProductRating
from shop.customers.models import Register

@app.route('/')
def home():
    page = request.args.get('page',1,type=int)
    products = AddProduct.query.filter(AddProduct.stock > 0).order_by(AddProduct.id.desc()).paginate(page=page, per_page=4)
    brands = Brand.query.join(AddProduct, (Brand.id == AddProduct.brand_id)).all()
    categories = Category.query.join(AddProduct, (Category.id == AddProduct.category_id)).all()
    return render_template('products/index.html', products=products, brands=brands, categories=categories)

@app.route('/product/<int:id>')
def single_page(id):
    product = AddProduct.query.get_or_404(id)
    ratings = ProductRating.query.all()
    brands = Brand.query.join(AddProduct, (Brand.id == AddProduct.brand_id)).all()
    categories = Category.query.join(AddProduct, (Category.id == AddProduct.category_id)).all()
    return render_template('products/single_page.html', product=product, brands=brands, categories=categories, ratings=ratings)


@app.route('/brand/<int:id>')
def get_brand(id):
    bran_id = Brand.query.filter_by(id=id).first_or_404()
    page = request.args.get('page', 1, type=int)
    brand = AddProduct.query.filter_by(brand=bran_id).paginate(page=page, per_page=1)
    brands = Brand.query.join(AddProduct, (Brand.id == AddProduct.brand_id)).all()
    categories = Category.query.join(AddProduct, (Category.id == AddProduct.category_id)).all()
    return render_template('products/index.html', brand=brand, brands=brands, categories=categories, bran_id=bran_id)

@app.route('/category/<int:id>')
def get_category(id):
    page = request.args.get('page', 1, type=int)
    cat_id = Category.query.filter_by(id=id).first_or_404()
    get_cat = AddProduct.query.filter_by(category=cat_id).paginate(page=page, per_page=1)
    brands = Brand.query.join(AddProduct, (Brand.id == AddProduct.brand_id)).all()
    categories = Category.query.join(AddProduct, (Category.id == AddProduct.category_id)).all()
    return render_template('products/index.html', get_cat=get_cat, categories=categories, brands=brands, cat_id=cat_id)

@app.route('/addbrand', methods=['GET', 'POST'])
def addbrand():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    if request.method == "POST":
        getbrand = request.form.get('brand')
        brand = Brand(name=getbrand)
        db.session.add(brand)
        flash(f'The Brand {getbrand} was added to your database', 'success')
        db.session.commit()
        return redirect(url_for('addbrand'))
    return render_template('products/addbrand.html', brands='brands')

@app.route('/updatetbrand/<int:id>', methods=['GET', 'POST'])
def updatetbrand(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    updatetbrand = Brand.query.get_or_404(id)
    brand = request.form.get('brand')
    if request.method == "POST":
        updatetbrand.name = brand
        flash(f'Your brand has been updated', 'success')
        db.session.commit()
        return redirect(url_for('brands'))
    return render_template('products/updatebrand.html', title="Update Brand Page", updatetbrand=updatetbrand)

@app.route('/deletebrand/<int:id>', methods=['POST'])
def deletebrand(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    brand = Brand.query.get_or_404(id)
    if request.method=="POST":
        db.session.delete(brand)
        db.session.commit()
        flash(f'The brand {brand.name} was deleted from your database', 'success')
        return redirect(url_for('admin'))
    flash(f'The brand {brand.name} cant be deleted from your database', 'warning')
    return redirect(url_for('admin'))


@app.route('/addcat', methods=['GET', 'POST'])
def addcat():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    if request.method == "POST":
        getbrand = request.form.get('category')
        cat = Category(name=getbrand)
        db.session.add(cat)
        flash(f'The Category {getbrand} was added to your database', 'success')
        db.session.commit()
        return redirect(url_for('addcat'))
    return render_template('products/addbrand.html')

@app.route('/updatecat/<int:id>', methods=['GET', 'POST'])
def updatecat(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    updatecat = Category.query.get_or_404(id)
    category = request.form.get('category')
    if request.method == "POST":
        updatecat.name = category
        flash(f'Your category has been updated', 'success')
        db.session.commit()
        return redirect(url_for('categories'))
    return render_template('products/updatebrand.html', title="Update Category Page", updatecat=updatecat)

@app.route('/deletecategory/<int:id>', methods=['POST'])
def deletecategory(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    category = Category.query.get_or_404(id)
    if request.method=="POST":
        db.session.delete(category)
        db.session.commit()
        flash(f'The category {category.name} was deleted from your database', 'success')
        return redirect(url_for('admin'))
    flash(f'The category {category.name} cant be deleted from your database', 'warning')
    return redirect(url_for('admin'))



@app.route('/Addproducts', methods=['GET', 'POST'])
def addproducts():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    brands = Brand.query.all()
    categories = Category.query.all()
    form = Addproduct(request.form)
    if request.method == "POST":
        name = form.name.data
        price = form.price.data
        discount = form.discount.data
        stock = form.stock.data
        colors = form.colors.data
        desc = form.description.data
        brand = request.form.get('brand')
        category = request.form.get('category')
        image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")
        image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")
        image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")

        addpro = AddProduct(name=name, discount=discount, price=price, stock=stock, colors=colors,
                             desc=desc, brand_id=brand, category_id=category, image_1=image_1, image_2=image_2, image_3=image_3)
        db.session.add(addpro)
        flash(f'The product {name} has been added to your database', 'success')
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('products/addproducts.html', title="Add Product", form=form, brands=brands,
                           categories=categories)

@app.route('/updateproduct/<int:id>', methods=['GET', 'POST'])
def updateproduct(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    brands = Brand.query.all()
    categories = Category.query.all()
    product = AddProduct.query.get_or_404(id)
    brand = request.form.get('brand')
    category = request.form.get('category')
    form = Addproduct(request.form)
    if request.method == 'POST':
        product.name = form.name.data
        product.price = form.price.data
        product.discount = form.discount.data
        product.brand_id = brand
        product.category_id = category
        product.colors = form.colors.data
        product.desc = form.description.data
        if request.files.get('image_1'):
            try:
                os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_1))
                product.image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")
            except:
                product.image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")

        if request.files.get('image_2'):
            try:
                os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_2))
                product.image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")
            except:
                product.image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")

        if request.files.get('image_3'):
            try:
                os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_3))
                product.image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")
            except:
                product.image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")

        db.session.commit()
        flash(f'Your product has been updated', 'success')
        return redirect(url_for('admin'))

    form.name.data = product.name
    form.price.data = product.price
    form.discount.data = product.discount
    form.stock.data = product.stock
    form.colors.data = product.colors
    form.description.data = product.desc

    return render_template('products/updateproduct.html', form=form, brands=brands, categories=categories, product=product)

@app.route('/deleteproduct/<int:id>', methods=['POST'])
def deleteproduct(id):
    product = AddProduct.query.get_or_404(id)
    if request.method == 'POST':
        try:
            os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_1))
            os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_2))
            os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_3))
        except Exception as e:
            print(e)

        db.session.delete(product)
        db.session.commit()
        flash(f'The product {product.name} was deleted from your record', 'success')
        return redirect(url_for('admin'))

    flash(f'cant delete the product {product.name}', 'danger')
    return redirect(url_for('admin'))

#----------------------------------------------------------------------------------------------------


# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import string

from collections import Counter
import nltk as nltk
nltk.download('stopwords')
nltk.download('vader_lexicon')

set(stopwords.words('english'))

@app.route('/sentiment/<int:id>')
def my_form(id):
    product = AddProduct.query.get_or_404(id)
    return render_template('products/form.html')

# @app.route('/sentiment', methods=['POST'])
# def my_form_post():
#    stop_words = stopwords.words('english')
#    text1 = request.form['text1'].lower()

#    processed_doc1 = ' '.join([word for word in text1.split() if word not in stop_words])

#    sa = SentimentIntensityAnalyzer()
#    dd = sa.polarity_scores(text=processed_doc1)
#    compound = round((1 + dd['compound'])/2, 2)

#    return render_template('customer/form.html', final=compound, text1=text1)


@app.route('/sentiment/<int:id>', methods=['POST'])
def my_form_post(id):
    global Rating
    product = AddProduct.query.get_or_404(id)

    if request.method == "POST":
        text1 = request.form['text1']
        product_name = product.name

        lower_case = text1.lower()
        cleaned_text = lower_case.translate(str.maketrans('', '', string.punctuation))

        # Using word_tokenize because it's faster than split()
        tokenized_words = word_tokenize(cleaned_text, "english")

        # Removing Stop Words
        final_words = []
        for word in tokenized_words:
            if word not in stopwords.words('english'):
                final_words.append(word)

        # Lemmatization - From plural to single + Base form of a word (example better-> good)
        lemma_words = []
        for word in final_words:
            word = WordNetLemmatizer().lemmatize(word)
            lemma_words.append(word)

        mydir = 'E:/sentiment_analysis/shop'
        myfile = 'emotions.txt'
        sentiment_emotions_txt = os.path.join(mydir, myfile)

        emotion_list = []
        with open(sentiment_emotions_txt, 'r') as file:
            for line in file:
                clear_line = line.replace("\n", '').replace(",", '').replace("'", '').strip()
                word, emotion = clear_line.split(':')

                if word in lemma_words:
                    emotion_list.append(emotion)

        print(emotion_list)
        w = Counter(emotion_list)
        print(w)

        score = SentimentIntensityAnalyzer().polarity_scores(cleaned_text)
        print(score)
    #  if score['neg'] > score['pos']:
    #      print("Negative Sentiment")
    #  elif score['neg'] < score['pos']:
    #      print("Positive Sentiment")
    #  else:
    #      print("Neutral Sentiment")

        if score['pos'] > score['neg']:
            if (score['pos'] > 0.0) and (score['pos'] < 0.1) and (score['neg'] >= 0.0) and (score['neg'] < 0.2):
                Rating = 1
            elif (score['pos'] > 0.1) and (score['pos'] < 0.2) and (score['neg'] >= 0.0) and (score['neg'] < 0.2):
                Rating = 3
            elif (score['pos'] > 0.2) and (score['pos'] < 0.3) and (score['neg'] >= 0.0) and (score['neg'] < 0.2):
                Rating = 4
            elif (score['pos'] > 0.3) and (score['neg'] >= 0.0) and (score['neg'] < 0.1):
                Rating = 5
        else:
            if (score['pos'] >= 0.0) and (score['pos'] < 0.3) and (score['neg'] > 0.0) and (score['neg'] < 0.1):
                Rating = 2
            elif (score['pos'] >= 0.0) and (score['pos'] < 0.3) and (score['neg'] > 0.1) and (score['neg'] < 0.3):
                Rating = 1.5
            elif (score['pos'] >= 0.0) and (score['pos'] < 0.3) and (score['neg'] > 0.3):
                Rating = 1

        ratings = ProductRating(Name=product_name, text1=text1, Rating=Rating)
        db.session.add(ratings)
        flash(f'The comment is added')
        db.session.commit()
        return redirect(url_for('single_page', id=product.id))

    return render_template('products/form.html')




