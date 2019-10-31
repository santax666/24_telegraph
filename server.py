from flask import Flask, render_template, request, make_response, g, redirect, url_for
from datetime import datetime
from binascii import crc32
import json

def read_articles():
    with open('articles.json','r') as articles_file:
        return json.load(articles_file)

def write_articles(articles):
    with open('articles.json','w') as articles_file:
        json.dump(articles, articles_file, ensure_ascii=False, indent=4)

def update_articles(article_hash,new_data):
    articles = read_articles()
    articles[article_hash] = new_data
    write_articles(articles)

def generate_hash_str(str_for_hash):
    return '{:08x}'.format(crc32(str_for_hash.encode('utf8')))

app = Flask(__name__)

@app.before_request
def get_now_datetime():
    g.now_str = datetime.now().strftime('%Y%m%d%H%M%f')
    g.user = request.cookies.get('userid')

@app.route('/', methods=['GET', 'POST'])
def form(error=''):
    article = request.form.to_dict()
    if g.user is None:
        user = generate_hash_str(g.now_str)
        response = make_response(render_template('form.html', form=article))
        response.set_cookie('userid',user)
        return response
    if request.method == 'POST':
        article_texts = article.values()
        if all(article_texts):
            hashstr = generate_hash_str(g.now_str+''.join(article_texts))
            article['userid']= g.user
            update_articles(hashstr,article)
            return redirect(url_for('show_article', hashstr=hashstr))
        else:
            error = 'Вы заполнили не все поля'
    return render_template('form.html', error=error, form=article)

@app.route('/<hashstr>', methods=['GET', 'POST'])
def show_article(hashstr):
    article = read_articles().get(hashstr)
    if article is None:
        return render_template('404.html')
    else:
        
        if request.method == 'POST' and 'edit' in request.form:
            return render_template('form.html', form=article)
        else:
            article.update(request.form.to_dict())
            update_articles(hashstr,article)
            owner = g.user == article['userid']
            return render_template('article.html', form=article, owner=owner)

if __name__ == "__main__":
    app.run(debug=True)
