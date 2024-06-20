import sqlite3
import logging
import sys

from logging.config import dictConfig

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    connection.execute('INSERT INTO connections DEFAULT VALUES')
    connection.commit()
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.info(f'Non existing article requested. ID: {post_id}')
        return render_template('404.html'), 404
    else:
        app.logger.info(f'Article "{post[2]}" retrieved!')
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About page retrieved!')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info(f'New article created: "{title}"!')
            return redirect(url_for('index'))

    return render_template('create.html')


# Healthcheck endpoint
# Build the /healthz endpoint for the TechTrends application. The endpoint should return the following response:
# - An HTTP 200 status code
# - A JSON response containing the 'result: OK - healthy' message
@app.route('/healthz')
def healthz():  
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )
    return response


# Metrics endpoint
# Build a /metrics endpoint that would return the following:
# - An HTTP 200 status code
# - A JSON response with the following metrics:
#   -  Total amount of posts in the database
#   -  Total amount of connections to the database. For example, accessing an article will query the database, hence will count as a connection.
# Example output: {"db_connection_count": 1, "post_count": 7}
# Tips: The /metrics endpoint response should NOT be hardcoded.
@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connections = connection.execute('SELECT * FROM connections').fetchall()
    connection.close()
    db_connection_count = len(connections)
    post_count = len(posts)
    response = app.response_class(
            response=json.dumps({"db_connection_count": db_connection_count, "post_count": post_count}),
            status=200,
            mimetype='application/json'
    )
    return response


# Logs
# Extend the TechTrends application to log the following events:
# - An existing article is retrieved. The title of the article should be recorded in the log line.
# - A non-existing article is accessed and a 404 page is returned.
# - The "About Us" page is retrieved.
# - A new article is created. The title of the new article should be recorded in the logline.
# Every log line should include the timestamp and be outputted to the STDOUT. Also, capture any Python logs at the DEBUG level.
# Example output of loglines:
# INFO:werkzeug:127.0.0.1 - - [08/Jan/2021 22:40:06] "GET /metrics HTTP/1.1" 200 -
# INFO:werkzeug:127.0.0.1 - - [08/Jan/2021 22:40:09] "GET / HTTP/1.1" 200 -
# INFO:app:01/08/2021, 22:40:10, Article "2020 CNCF Annual Report" retrieved!

# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    # https://flask.palletsprojects.com/en/2.3.x/logging/#basic-configuration
    dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
    })
    app.run(host='0.0.0.0', port=3111)
