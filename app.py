######################################
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
from datetime import datetime
import pymysql
from pymysql import converters

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460cs460'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		first_name=request.form.get('first name')
		last_name=request.form.get('last name')
		date_of_birth=request.form.get('date of birth')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	hometown=request.form.get('hometown')
	gender=request.form.get('gender')
	
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name, date_of_birth, homeTown, gender, user_id) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')".format(email, password, first_name, last_name, date_of_birth, hometown, gender, user_id)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print(email + " is not unique")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
	
def does_User_searched_exits(email):
	#"use this to check if a email searched by a user exits in User() table
	cursor = conn.cursor()
	if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(email)):
		#this means the email searched exists in the database
		return True
	else:
		return False

def listallFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT Users.user_id, Friends_with.user2_id FROM Users, Friends_with WHERE Friends_with.user1_id = '{0}'".format(uid))
	results = cursor.fetchall()
	friend_list = [friend[1] for friend in results]
	return friend_list

def num_of_Pictures_of_User(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(Pictures.picture_id) FROM Pictures, Users WHERE Pictures.user_id=Users.user_id AND Users.user_id = '{0}'".format(uid))
	result_1 = cursor.fetchone()
	num_picture = result_1[0]
	return num_picture
	
def num_of_Comments_of_User(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(Comment.comment_id) FROM USERS, User_has_comment, Comment, Commented_on, Picures WHERE Users.user_id=User_has_comment.user_id AND User_has_comment.comment_id=Comment.comment_id=COmmented_on.comment_id AND Commented_on.picture_id=Pictures.picture_id AND Users.user_id!=Pictures.user_id AND User.user_id='{0}'".format(uid))
	result_1 = cursor.fetchone()
	num_comment = result_1[0]
	return num_comment

def cal_User_activity(uid):
	num_picture = num_of_Pictures_of_User(uid)
	num_comment = num_of_Comments_of_User(uid)
	score = num_picture + num_comment
	return score

def not_self_comment(uid, puid):
	cursor = conn.cursor()
	if cursor.execute("SELECT User.user_id FROM User, Pictures WHERE User.user_id=Pictures.user_id AND User.user_id='{0}' AND Pictures.user_id='{1}'".format(uid, puid)):
		return False
	else:
		return True

def search_Comment_Users(text):
	cursor = conn.cursor
	cursor.execute("SELECT User.user_id, COUNT(Comment.text) as count FROM User, Comment WHERE Comment.user_id = User.user_id AND Comment.text = '{0}' ORDER BY count DESC".format(text))
	return cursor.fetchall()

def possible_new_Friends(uid):
	friends = listallFriends(uid)
	possible_new_friends = []
	for friend in friends:
		friends_of_friend = listallFriends(friend)
		for f in friends_of_friend:
			if f not in possible_new_friends and f not in friends:
				possible_new_friends+=f
	return possible_new_friends
	


def pull_album(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, name FROM Albums WHERE owner_id = '{0}'".format(uid))
	return cursor.fetchall()

def pull_new_pic_id(uid):
	cursor = conn.cursor()
	result=cursor.execute("SELECT picture_id FROM Pictures WHERE user_id = '{0}'".format(uid))
	while result is not None:
		output=result
		result=cursor.fetchone()
	return output

def pullNewCid(uid):
	cursor=conn.cursor()
	result=cursor.execute("SELECT comment_id FROM Comment WHERE user_id = '{0}'".format(uid))
	while result is not None:
		output=result
		result=cursor.fetchone()
	return output


def pid_in_album(aid):
    cursor = conn.cursor()
    cursor.execute("SELECT picture_id FROM Photo_in_album WHERE album_id = '{0}'".format(aid))
    results = cursor.fetchall()
    pidList = [result[0] for result in results]
    return pidList


def picture_in_album(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT Pictures.imgdata, Pictures.picture_id, Pictures.caption FROM Pictures,Photo_in_album WHERE Pictures.picture_id=Photo_in_album.picture_id AND Photo_in_album.album_id = '{0}'".format(aid))
	return cursor.fetchall()

def getAllUsers():
	cursor = conn.cursor()
	cursor.execute("SELECT user_id, email FROM Users")
	return cursor.fetchall()

def getAllTags():
	cursor = conn.cursor()
	cursor.execute("SELECT content FROM Tags")
	results = cursor.fetchall()
	tagList=[tags[0] for tags in results]
	return tagList

def allPhotoWithTag(content):
	cursor = conn.cursor()
	cursor.execute("SELECT Pictures.imgdata, Pictures.picture_id, Pictures.caption FROM Pictures, photo_has_tags WHERE Pictures.picture_id=photo_has_tags.picture_id AND photo_has_tags.content='{0}'".format(converters.escape_string(content)))
	return cursor.fetchall()

def userPhotoWithTag(uid,content):
	cursor = conn.cursor()
	cursor.execute("SELECT Pictures.imgdata, Pictures.picture_id, Pictures.caption FROM Pictures, photo_has_tags WHERE Pictures.picture_id=photo_has_tags.picture_id AND photo_has_tags.content='{0}' AND Pictures.user_id='{1}'".format(converters.escape_string(content),uid))
	return cursor.fetchall()

def getUserTags(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT photo_has_tags.content FROM photo_has_tags, Pictures WHERE Pictures.picture_id=photo_has_tags.picture_id AND Pictures.user_id='{0}'".format(uid))
	results = cursor.fetchall()
	tagList=[tags[0] for tags in results]
	return tagList

def getTrendingTags():
    cursor = conn.cursor()
    cursor.execute("SELECT content, COUNT(*) as count FROM photo_has_tags GROUP BY content ORDER BY count DESC LIMIT 3")
    results = cursor.fetchall()
    tagList = [tags[0] for tags in results]
    return tagList
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/add_friend', methods=['GET', 'POST'])
@flask_login.login_required
def add_new_Friend():
	if request.method == 'POST':
			femail = request.form.get('email_of_the_new_friend')
			fid = getUserIdFromEmail(femail)
			uid = getUserIdFromEmail(flask_login.current_user.id)
			if does_User_searched_exits(femail):
				cursor = conn.cursor()
				cursor.execute('''INSERT INTO Friends_with (user1_id, user2_id) VALUES (%s, %s)''', (uid, fid))
				conn.commit()
				return render_template('hello.html', name=flask_login.current_user.id, message='new friend added!')
			else:
				print('the new friend email entered is not valid')
				return flask.redirect(flask.url_for('add_friend'))
	else:
			return flask.redirect(flask.url_for('add_friend'))

	
@app.route('/friendlist', methods=['GET'])
@flask_login.login_required
def showFriendslist():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friendlist.html', Friends=listallFriends(uid))

@app.route('/leaving_comments/<pid>', methods=['GET', 'POST'])
def leave_comments(pid):
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        comment = request.form.get('commentContent')
        comment_time = datetime.now()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Comment (text, user_id, comment_day) VALUES (%s, %s, %s)''', (comment, uid, comment_time))
        conn.commit()
        cid=pullNewCid(uid)
        cursor.execute('''INSERT INTO Commented_on (comment_id,picture_id) VALUES(%s, %s)''',(cid,pid))
        cursor.execute('''INSERT INTO User_has_comment (comment_id, user_id) VALUES(%s, %s)''',(cid,uid))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id, message='comment posted!')
    else:
        return render_template('newComment.html')
		
@app.route('/searchcomment', methods=['GET'])
@flask_login.login_required
def list_search_comments():
	text = request.form.get('comment content')
	return render_template('searchcomment.html', Users=search_Comment_Users(text))

@app.route('/friendrecommend', methods=['GET'])
@flask_login.login_required
def friend_recommend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friendrecommend.html',Friends=possible_new_Friends(uid))
	


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		aid = request.form.get('album')
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		tags=request.form.get('tags')
		tagList=tags.split()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption) VALUES (%s, %s, %s )''', (photo_data, uid, caption))
		conn.commit()
		pid=pull_new_pic_id(uid)
		for item in tagList:
			cursor.execute("SELECT content FROM Tags WHERE content='{0}'".format(item))
			result=cursor.fetchone()
			if result is None:
				cursor.execute('''INSERT INTO Tags(content) VALUES (%s)''',(item))
				conn.commit()
			cursor.execute('''INSERT INTO photo_has_tags(content,picture_id) VALUES (%s, %s)''',(item, pid))
		cursor.execute('''INSERT INTO Photo_in_album(picture_id, album_id) VALUES (%s, %s)''',(pid,aid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		aid_options = pull_album(uid)
		return render_template('upload.html', aid_options=aid_options)
#end photo uploading code


	
@app.route('/create_album', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        name = request.form.get('album_name')
        current_time = datetime.now()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Albums (name, owner_id, doc) VALUES (%s, %s, %s)''', (name, uid,current_time))
        conn.commit()
        return flask.redirect(flask.url_for('upload_file'))
    else:
        return render_template('create_album.html')

@app.route('/userAlbum', methods=['GET'])
@flask_login.login_required
def userAlbum():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    return redirect(f"/album/{uid}")


@app.route('/album/<uid>', methods=['GET', 'POST'])
@flask_login.login_required
def album(uid):
	if request.method == 'POST':
		aid=request.form.get('album')
		return(render_template('album.html',photos=picture_in_album(aid),base64=base64))

	else:
		aid_options = pull_album(uid)
		return render_template('albumList.html',aid_options=aid_options)
	

@app.route('/remove_album', methods=['GET', 'POST'])
@flask_login.login_required
def remove_album():
	if request.method == 'POST':
		aid = request.form.get('album')
		cursor = conn.cursor()
		result=cursor.execute("SELECT Pictures.picture_id FROM Pictures,Photo_in_album WHERE Photo_in_album.album_id = '{0}'".format(aid))
		print(result, flush=True)
		picList=pid_in_album(aid)
		for pid in picList:
			cursor.execute('''DELETE FROM Photo_in_album WHERE picture_id=%s''',(pid))
			cursor.execute('''DELETE FROM Pictures WHERE picture_id=%s''',(pid))
		cursor.execute('''DELETE FROM Albums WHERE album_id=%s''', (aid))
		conn.commit()
		return flask.redirect(flask.url_for('upload_file'))
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		aid_options = pull_album(uid)
		return render_template('remove_album.html',aid_options=aid_options)
		
@app.route("/Oalbum", methods=['GET'])
def viewPhoto():
	return render_template ('UserList.html',Users=getAllUsers())

@app.route("/OTags", methods=['GET'])
def viewTag():
	return render_template('tags.html',Tags=getAllTags(),message="All Tags")

@app.route("/TagPic/<Tag>", methods=['GET'])
def TagPic(Tag):
	return(render_template('album.html',photos=allPhotoWithTag(Tag),base64=base64))

@app.route("/myTags", methods=['GET'])
@flask_login.login_required
def viewMyTag():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('mytags.html',Tags=getUserTags(uid),message="Your Tags")

@app.route("/myTagPic/<Tag>", methods=['GET'])
@flask_login.login_required
def userPicTag(Tag):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return(render_template('album.html',photos=userPhotoWithTag(uid,Tag),base64=base64))

@app.route("/trendingTags", methods=['GET'])
def popularTags():
	return render_template('tags.html',Tags=getTrendingTags(),message="Trending Tags")

@app.route("/searchTags", methods=['GET','POST'])
def searchTags():
	if request.method == 'POST':
		tags=request.form.get('Tag')
		tagList=tags.split()
		picList=[]
		for item in tagList:
			picList+=allPhotoWithTag(item)
		distinctPicList=list(set(picList))
		return render_template('album.html', photos=distinctPicList,base64=base64)
	else:
		return render_template('searchTag.html')




	





#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')



if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
