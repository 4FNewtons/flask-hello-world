from flask import Flask, render_template, url_for, request, make_response, redirect, jsonify
from datetime import date, datetime
import os, io
import json
import subprocess

import dropbox

import sqlite3

app = Flask(__name__)

access_token = os.environ.get('DROPBOX_TOKEN')
dbx = dropbox.Dropbox(access_token)

local_file_path = os.path.dirname(os.path.abspath(__file__))+ '/static/dbs/main.db'
dropbox_file_path = '/main.db'

def get_comments_html(comments_list):
  comments_html = ""
  for comment in comments_list:
    data_list = comment.split(':')
    author = data_list[0].strip()
    value = data_list[1].strip()
    comment_html = f'<div class="ein-comment"><h3 class="comment-autor">{author}</h3><p class="comment-value">{value}</p></div>'
    comments_html += comment_html
  return comments_html


def get_comments_for_post(post_id):
  try:
    conn = sqlite3.connect(local_file_path)
    cur = conn.cursor()
    cur.execute("SELECT comments FROM posts WHERE id = ?", (post_id, ))
    result = cur.fetchone()
    conn.close()
    return result[0].split("|||") if result is not None else []
  except Exception:
    return []


def add_comment_to_post(post_id, new_comment):
  existing_comments = get_comments_for_post(post_id)
  existing_comments.append(new_comment)
  updated_comments = "|||".join(existing_comments)

  conn = sqlite3.connect(local_file_path)
  cur = conn.cursor()
  cur.execute("UPDATE posts SET comments = ? WHERE id = ?",
              (updated_comments, post_id))
  conn.commit()
  conn.close()
  with open(local_file_path, 'rb') as f:
    dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode("overwrite"))

  print("Файл успешно загружен на Dropbox")


@app.route('/add_comment', methods=['POST'])
def add_comment():
  data = request.get_json()
  post_id = data['post_id']
  author = data['author']
  text = data['text']

  new_comment = f"{author}: {text}"
  add_comment_to_post(post_id, new_comment)

  comments_list = get_comments_for_post(post_id)
  comments_html = get_comments_html(comments_list)

  return jsonify({'comments': comments_html})


@app.route('/get_comments', methods=['GET'])
def get_comments():
  post_id = request.args.get('post_id')

  comments_list = get_comments_for_post(post_id)
  comments_html = get_comments_html(comments_list)

  return jsonify({'comments': comments_html})


@app.route('/your-endpoint', methods=['POST'])
def your_endpoint():
  data = request.get_json()
  print(data)
  if data['action'] == 'like':
    conn = sqlite3.connect(local_file_path)
    cur = conn.cursor()
    cur.execute("SELECT like_people, dislike_people FROM posts WHERE id = ?",
                (data['id'], ))
    result = cur.fetchone()
    like_people = result[0] if result is not None else None
    dislike_people = result[1] if result is not None else None

    if like_people is not None:
      like_people_list = like_people.split(", ") if isinstance(
        like_people, str) else []
      print(like_people_list)
      if data['name'] in like_people_list:
        like_people_list.remove(data['name'])
        like_people = ", ".join(like_people_list) if like_people_list else ""
        cur.execute(
          "UPDATE posts SET likes = likes - 1, like_people = ? WHERE id = ?",
          (like_people, data['id']))
        conn.commit()
      else:
        if data['name'] != None:
            like_people_list.append(data['name'])
            like_people = ", ".join(like_people_list)
            cur.execute(
            "UPDATE posts SET likes = likes + 1, like_people = ? WHERE id = ?",
            (like_people, data['id']))

            conn.commit()
            with open(local_file_path, 'rb') as f:
                dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode("overwrite"))

                print("Файл успешно загружен на Dropbox")
        else:
          pass

      cur.execute("SELECT likes, dislikes FROM posts WHERE id = ?",
                  (data['id'], ))
      result = cur.fetchone()
      count_of_likes = result[0]
      count_of_dislikes = result[1]

      response = {
        'message': 'Success',
        'likes': count_of_likes,
        'dislikes': count_of_dislikes
      }
      return jsonify(response)
    else:
      cur.execute(
        "UPDATE posts SET likes = likes + 1, like_people = ? WHERE id = ?",
        (data['name'], data['id']))
      with open(local_file_path, 'rb') as f:
        dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode("overwrite"))
        print("Файл успешно загружен на Dropbox")

      if dislike_people is not None and data['name'] in dislike_people.split(
          ", "):
        dislike_people_list = dislike_people.split(", ")
        dislike_people_list.remove(data['name'])
        dislike_people = ", ".join(
          dislike_people_list) if dislike_people_list else ""
        cur.execute(
          "UPDATE posts SET dislikes = dislikes - 1, dislike_people = ? WHERE id = ?",
          (dislike_people, data['id']))

      conn.commit()

      cur.execute("SELECT likes, dislikes FROM posts WHERE id = ?",
                  (data['id'], ))
      result = cur.fetchone()
      print(result)
      count_of_likes = result[0]
      count_of_dislikes = result[1]

      response = {
        'message': 'Success',
        'likes': count_of_likes,
        'dislikes': count_of_dislikes
      }
      return jsonify(response)

  if data['action'] == 'dislike':
    conn = sqlite3.connect(local_file_path)
    cur = conn.cursor()
    cur.execute("SELECT like_people, dislike_people FROM posts WHERE id = ?",
                (data['id'], ))
    result = cur.fetchone()
    like_people = result[0] if result is not None else None
    dislike_people = result[1] if result is not None else None

    if dislike_people is not None:
      dislike_people_list = dislike_people.split(", ") if isinstance(
        dislike_people, str) else []
      if data['name'] in dislike_people_list:
        dislike_people_list.remove(data['name'])
        dislike_people = ", ".join(
          dislike_people_list) if dislike_people_list else ""
        cur.execute(
          "UPDATE posts SET dislikes = dislikes - 1, dislike_people = ? WHERE id = ?",
          (dislike_people, data['id']))
        conn.commit()
      else:
        dislike_people_list.append(data['name'])
        dislike_people = ", ".join(dislike_people_list)
        cur.execute(
          "UPDATE posts SET dislikes = dislikes + 1, dislike_people = ? WHERE id = ?",
          (dislike_people, data['id']))

        if like_people is not None and data['name'] in like_people.split(", "):
          like_people_list = like_people.split(", ")
          like_people_list.remove(data['name'])
          like_people = ", ".join(like_people_list) if like_people_list else ""
          cur.execute(
            "UPDATE posts SET likes = likes - 1, like_people = ? WHERE id = ?",
            (like_people, data['id']))

        conn.commit()

      cur.execute("SELECT likes FROM posts WHERE id = ?", (data['id'], ))
      result = cur.fetchone()
      count_of_likes = result[0]

      response = {
        'message': 'Success',
        'likes': count_of_likes,
      }
      return jsonify(response)
    else:
      cur.execute(
        "UPDATE posts SET dislikes = dislikes + 1, dislike_people = ? WHERE id = ?",
        (data['name'], data['id']))

      if like_people is not None and data['name'] in like_people.split(", "):
        like_people_list = like_people.split(", ")
        like_people_list.remove(data['name'])
        like_people = ", ".join(like_people_list) if like_people_list else ""
        cur.execute(
          "UPDATE posts SET likes = likes - 1, like_people = ? WHERE id = ?",
          (like_people, data['id']))

      conn.commit()

      cur.execute("SELECT likes, dislikes FROM posts WHERE id = ?",
                  (data['id'], ))
      result = cur.fetchone()
      if result is not None:
        count_of_likes = result[0]
        count_of_dislikes = result[1]

        response = {
          'message': 'Success',
          'likes': count_of_likes,
        }
        return jsonify(response)
      else:
        response = {'message': 'Success', 'likes': 0}
        return jsonify(response)


@app.route('/', methods=['GET', 'POST'])
def index():

  message = ''

  postlist_str = '<h3 style="font-family: Inter; text-align: center; color: gray;">Тут пока пусто...</h3>'

  username = request.cookies.get('username')

  current_date = date.today()

  creating_date = date.today()
  creating_time = str(datetime.now().hour) + ':' + str(
    datetime.now().minute) + ':' + str(datetime.now().second)

  conn = sqlite3.connect(local_file_path)
  cur = conn.cursor()
  cur.execute('''CREATE TABLE IF NOT EXISTS users(
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE,
                  email TEXT NOT NULL UNIQUE,
                  password TEXT,
                  joining_date datetime,
                  rate INTEGER,
                  articles TEXT,
                  country TEXT);''')
  conn.commit()
  cur.execute('''CREATE TABLE IF NOT EXISTS posts(
                  id INTEGER PRIMARY KEY,
                  autor TEXT,
                  title TEXT NOT NULL,
                  preview TEXT NOT NULL,
                  description TEXT NOT NULL,
                  creating_date datetime,
                  creating_time timestamp,
                  likes INTEGER,
                  like_people TEXT,
                  dislikes INTEGER,
                  dislike_people TEXT,
                  comments TEXT);''')
  conn.commit()
  cur.close()

  conn = sqlite3.connect(local_file_path)
  cur = conn.cursor()

  if request.method == 'POST':
    form_type = request.form.get('form_type')
    if form_type == 'register':
      username = request.form['username']
      email = request.form['email']
      password = request.form['password']
      confirm_password = request.form['confirm_password']

      conn = sqlite3.connect(local_file_path)
      cur = conn.cursor()
      cur.execute("SELECT * FROM users WHERE name = ?", (username, ))
      result = cur.fetchone()
      if result:
        message = 'Пользователь с таким логином уже существует'
      else:
        cur.execute("SELECT * FROM users WHERE email = ?", (email, ))
        result = cur.fetchone()
        if result:
          message = 'Пользователь с такой почтой уже существует'
        else:
          cur.execute(
            "INSERT INTO users (name, email, password, joining_date) VALUES (?, ?, ?, ?)",
            (username, email, password, current_date))
          conn.commit()
          cur.close()
          with open(local_file_path, 'rb') as f:
            dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode("overwrite"))
            print("Файл успешно загружен на Dropbox")

          response = make_response(redirect('/'))
          response.set_cookie('username', username)
          return response
    elif form_type == 'login':
      username = request.form['username']
      password = request.form['password']
      print(username, password)

      conn = sqlite3.connect(local_file_path)
      cur = conn.cursor()
      cur.execute("SELECT * FROM users WHERE name = ? AND password = ?",
                  (username, password))
      result = cur.fetchone()
      print(result)
      if result:
        response = make_response(redirect('/'))
        response.set_cookie('username', username)
        return response
      else:
        message = 'Неправильный логин или пароль'

    if form_type == 'post':
      title = request.form['title']
      preview = request.form['preview']
      description = request.form['description']

      cur.execute(
        "INSERT INTO posts (autor, title, preview, description, creating_date, creating_time, likes, dislikes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (username, title, preview, description, creating_date, creating_time,
         0, 0))
      conn.commit()
      with open(local_file_path, 'rb') as f:
            dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode("overwrite"))
            print("Файл успешно загружен на Dropbox")
      cur.execute("SELECT articles FROM users WHERE name = ?", (username, ))
      result = cur.fetchone()
      if result is not None and result[0] is not None:
        posts_list = json.loads(result[0])
      else:
        posts_list = []

      posts_list.append(cur.lastrowid)
      cur.execute("UPDATE users SET articles = ? WHERE name = ?",
                  (json.dumps(posts_list), username))
      conn.commit()
      conn.close()

      return redirect('/')

  conn = sqlite3.connect(local_file_path)
  cur = conn.cursor()
  cur.execute("SELECT COUNT(*) FROM posts")
  result = cur.fetchone()
  print(result)
  conn.close()

  postlist = []
  postsdesc = []

  if result[0] > 0:
    conn = sqlite3.connect(local_file_path)
    cur = conn.cursor()
    cur.execute(
      "SELECT title, preview, autor, id, description, creating_date, likes, comments FROM posts ORDER BY id DESC"
    )
    result = cur.fetchall()

    titles_from_db = list([row[0] for row in result])
    previews_from_db = list([row[1] for row in result])
    autors_from_db = list([row[2] for row in result])
    ids_from_db = list([row[3] for row in result])
    descriptions_from_db = list([row[4] for row in result])
    date_from_db = list([row[5] for row in result])
    likes_from_db = list([row[6] for row in result])
    comments_from_db = list(
      [row[7] if row[7] is not None else 0 for row in result])
    conn.close()

    for i in range(len(titles_from_db)):
      ein_project = f'''<div class="ein-project">
            <div style="display: flex; justify-content: space-between; padding: 0 5%;">
                <div>
                    <h1 style="font-family: Inter; margin-bottom: 5px;">{titles_from_db[i]}</h1>
                    <h6 style="font-family: Inter; margin: 0;">{date_from_db[i]}</h6>
                </div>
                <div style="display: flex;">
                    <img src="" alt="">
                    <h4 style="font-family: Inter;">{autors_from_db[i]}</h4>
                </div>
            </div>
            <div style="padding: 0 5%;">
                <p class="article-text">{previews_from_db[i]}</p>
            </div>
            <div style="display: flex; margin-top: 5%;">
                <a data-post-id="{ids_from_db[i]}" class="more_button" onclick="OpenPost()">ЧИТАТЬ ДАЛЬШЕ</a>
            </div>
            <div class="l-panel">
                <div class="inl-panel">
                    <div onclick="Like(event)" data-like-id="{ids_from_db[i]}" class="panel-button like-panel-button">
                        <img data-like-id="{ids_from_db[i]}" id="like" class="like" src="/static/images/like_new.png">
                        <label data-like-id="{ids_from_db[i]}" class="count-likes" id="labelOfLikes{ids_from_db[i]}" for="like">{likes_from_db[i]}</label>
                    </div>
                    <div onclick="OpenComments(event)" data-comment-id="{ids_from_db[i]}" class="panel-button">
                      <img id="comments" data-comment-id="{ids_from_db[i]}" class="comments" src="/static/images/comments_new.png">
                      <label data-comment-id="{ids_from_db[i]}" class="count-likes" id="labelOfLikes{ids_from_db[i]}" for="comments">{len(get_comments_for_post(ids_from_db[i]))}</label>
                  </div>
                </div>
            </div>
        </div>'''
      postlist.append(ein_project)

    postlist_str = "".join(postlist)

    for i in range(len(titles_from_db)):
      ein_project_post = f'''<div id="post{ids_from_db[i]}" class="ein-project-post">
          <span class="close" onclick="closePopup()" style="position: absolute; right: 2%; top: 1%; font-size: 2em;">×</span>
          <div style="display: flex; justify-content: space-between;">
            <h1 style="font-family: Inter;">{titles_from_db[i]}</h1>
            <div style="display: flex;">
              <img src="" alt="">
              <h4 style="font-family: Inter;">{autors_from_db[i]}</h4>
            </div>
          </div>
          <div>
            <p class="article-text">{previews_from_db[i]}</p>
          </div>
          {descriptions_from_db[i]}
        </div>'''
      postsdesc.append(ein_project_post)
    postsdesc = json.dumps(postsdesc)
  else:
    print('Невозможно связаться с БД')

  return render_template('index.html',
                         username=username,
                         posts=postlist_str,
                         list_of_projects=postsdesc,
                         message=message)


@app.route('/about')
def about():
  username = request.cookies.get('username')
  return render_template('about.html', username=username)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
  message = ''
  current_date = date.today()
  if request.method == 'POST':
    form_type = request.form.get('form_type')
    if form_type == 'register':
      username = request.form['username']
      email = request.form['email']
      password = request.form['password']
      confirm_password = request.form['confirm_password']

      conn = sqlite3.connect(local_file_path)
      cur = conn.cursor()
      cur.execute("SELECT * FROM users WHERE name = ?", (username, ))
      result = cur.fetchone()
      if result:
        message = 'Пользователь с таким логином уже существует'
      else:
        cur.execute("SELECT * FROM users WHERE email = ?", (email, ))
        result = cur.fetchone()
        if result:
          message = 'Пользователь с такой почтой уже существует'
        else:
          cur.execute(
            "INSERT INTO users (name, email, password, joining_date) VALUES (?, ?, ?, ?)",
            (username, email, password, current_date))
          conn.commit()
          cur.close()
          with open(local_file_path, 'rb') as f:
            dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode("overwrite"))
            print("Файл успешно загружен на Dropbox")

          response = make_response(redirect('/'))
          response.set_cookie('username', username)
          return response
    elif form_type == 'login':
      username = request.form['username']
      password = request.form['password']
      print(username, password)

      conn = sqlite3.connect(local_file_path)
      cur = conn.cursor()
      cur.execute("SELECT * FROM users WHERE name = ? AND password = ?",
                  (username, password))
      result = cur.fetchone()
      print(result)
      if result:
        response = make_response(redirect('/'))
        response.set_cookie('username', username)
        return response
      else:
        message = 'Неправильный логин или пароль'

  return render_template('registration.html', message=message)


@app.route('/test')
def tests():
  return render_template('test.html')

if __name__ == '__main__':
    flask_process = subprocess.Popen(["python", "main.py"])

    flask_process.wait()