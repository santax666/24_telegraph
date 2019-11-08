from flask import Flask, render_template, request, g, redirect, url_for, abort, after_this_request
from os import urandom
import json

FORBIDDEN = 403
NOT_FOUND = 404


def generate_hash():
    len_of_hash = 4
    return urandom(len_of_hash).hex()


def validate_form_data(texts):
    min_len_of_text = 4
    err_msg = ('Поля содержат только числа', 'Текст в полях слишком короткий')
    numbers = ', '.join([i for i in texts if i.isdigit()])
    short_texts = ', '.join([i for i in texts if len(i) < min_len_of_text])
    errors = dict(zip(err_msg, (numbers, short_texts)))
    return dict(filter(lambda x: x[1], errors.items()))


def read_articles():
    with open('articles.json', 'r') as articles_file:
        return json.load(articles_file)


def write_articles(articles):
    with open('articles.json', 'w') as articles_file:
        json.dump(articles, articles_file, ensure_ascii=False)


def add_article(new_article):
    article_hash = generate_hash()
    update_article(article_hash, new_article)
    return article_hash


def update_article(article_hash, edited_article):
    articles = read_articles()
    articles.setdefault(article_hash, {}).update(edited_article)
    write_articles(articles)


app = Flask(__name__)


@app.before_first_request
def create_articles_file():
    with open('articles.json', 'w') as articles_file:
        articles_file.write('{}')


@app.before_request
def get_now_datetime_and_user():
    g.user = request.cookies.get('userid')
    if g.user is None:
        g.user = generate_hash()
        @after_this_request
        def remember_user(response):
            response.set_cookie('userid', g.user)
            return response


@app.route('/', methods=['GET', 'POST'])
def show_main_page():
    article = request.form.to_dict()
    errors = validate_form_data(article.values())
    if request.method == 'POST' and (not errors):
        article['userid'] = g.user
        article_hash = add_article(article)
        return redirect(url_for('show_article', article_hash=article_hash))
    return render_template('form.html', errors=errors, **article)


@app.route('/<article_hash>')
def show_article(article_hash):
    article = read_articles().get(article_hash) or abort(NOT_FOUND)
    return render_template('article.html', hash_str=article_hash, **article)


@app.route('/<article_hash>/edit', methods=['GET', 'POST'])
def edit_article(article_hash):
    article = read_articles().get(article_hash) or abort(NOT_FOUND)
    g.user == article['userid'] or abort(FORBIDDEN)
    if request.method == 'POST':
        update_article(article_hash, request.form.to_dict())
        return redirect(url_for('show_article', article_hash=article_hash))
    return render_template('form.html', **article)


if __name__ == "__main__":
    app.run(debug=True)
