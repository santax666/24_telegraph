from flask import Flask, render_template, request, g, redirect, url_for, abort, after_this_request
from validator_collection.checkers import has_length, is_numeric
from os import urandom
import json

FORBIDDEN = 403
NOT_FOUND = 404
DEBUG_MODE = False


def generate_hash():
    len_of_hash = 4
    return urandom(len_of_hash).hex()


def invalid_count_of_fields(fields, correct_count=3):
    return len(fields) != correct_count


def has_unknown_fields(fields):
    req_fields = ('header', 'signature', 'body')
    return any([i not in req_fields for i in fields])


def form_has_digits(texts):
    return any(map(is_numeric, texts))


def has_short_texts(texts, min_text_len=4):
    return not all(map(lambda x: has_length(x, minimum=min_text_len), texts))


def validate_form_data(article):
    fields, texts = article.keys(), article.values()
    return any((invalid_count_of_fields(fields), has_unknown_fields(
        fields), form_has_digits(texts), has_short_texts(texts)))


def read_articles():
    try:
        with open('articles.json', 'r') as articles_file:
            return json.load(articles_file)
    except FileNotFoundError:
        return {}


def write_articles(articles):
    with open('articles.json', 'w') as articles_file:
        json.dump(articles, articles_file, ensure_ascii=False)


def update_articles(article_hash, article_text):
    articles = read_articles()
    hash_str = article_hash or generate_hash()
    articles.setdefault(hash_str, {}).update(article_text)
    write_articles(articles)
    return hash_str


def show_edit_article_form(article, article_hash=''):
    errors = article and validate_form_data(article)
    if request.method == 'POST' and (not errors):
        article['userid'] = g.user
        hash_str = update_articles(article_hash, article)
        return redirect(url_for('show_article', article_hash=hash_str))
    return render_template('form.html', errors=errors, **article)


app = Flask(__name__)


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
    return show_edit_article_form(article)


@app.route('/<article_hash>/edit', methods=['GET', 'POST'])
def edit_article(article_hash):
    article = read_articles().get(article_hash) or abort(NOT_FOUND)
    g.user == article.pop('userid', '') or abort(FORBIDDEN)
    article_for_edit = request.form.to_dict() or article
    return show_edit_article_form(article_for_edit, article_hash)


@app.route('/<article_hash>')
def show_article(article_hash):
    article = read_articles().get(article_hash) or abort(NOT_FOUND)
    return render_template('article.html', hash_str=article_hash, **article)


if __name__ == "__main__":
    app.run(debug=DEBUG_MODE)
