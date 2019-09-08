from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, City, RestaurantItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

with app.open_resource('client_secrets.json') as f:
	CLIENT_ID = json.load(f)['web']['client_id']

#CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
#	'web']['client_id']
APPLICATION_NAME = "Vegan Dining"

# Connect to Database and create database session
engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(
	open('/var/www/html/ItemCatalog/fb_client_secrets.json', 'r').read())['web']['app_id']

    app_secret = json.loads(
        open('/var/www/html/ItemCatalog/fb_client_secrets.json', 'r').read())['web']['app_secret']

#    with app.open_resource('fb_client_secrets.json') as f:
#       app_id = json.load(f)['web']['app_id']
#
#    with app.open_resource('fb_client_secrets.json') as f:
#        app_id = json.load(f)['web']['app_id']

    url = 'https://graph.facebook.com/oauth/access_token?'
    url += 'grant_type=fb_exchange_token&client_id=%s' % app_id
    url += '&client_secret=%s' % app_secret
    url += '&fb_exchange_token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we
        have to split the token first on commas and select the first index
        which gives us the key : value for the server access token then we
        split it on colons to pull out the actual token value and replace the
        remaining quotes with nothing so that it can be used directly in the
        graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')


    url = 'https://graph.facebook.com/v2.8/me?access_token='
    url += '%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token='
    url += '%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;'
    output += 'border-radius: 150px;-webkit-border-radius: 150px;'
    output += '-moz-border-radius: 150px;"> '
    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as e:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = "make_response(json.dumps('Failed to revoke"
        response += " token for given user.', 400))"
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view city Information
@app.route('/city/<int:city_id>/restaurants/JSON')
def restaurantJSON(city_id):
    city = session.query(City).filter_by(id=city_id).one()
    items = session.query(RestaurantItem).filter_by(
        city_id=city_id).all()
    return jsonify(RestaurantItems=[i.serialize for i in items])


@app.route('/city/<int:city_id>/restaurants/<int:restaurant_id>/JSON')
def restaurantItemJSON(city_id, restaurant_id):
    Restaurant_Item = session.query(RestaurantItem).filter_by(
        id=restaurant_id).one()
    return jsonify(Restaurant_Item=Restaurant_Item.serialize)


@app.route('/city/JSON')
def citiesJSON():
    cities = session.query(City).all()
    return jsonify(cities=[c.serialize for c in cities])


# Show all cities
@app.route('/')
@app.route('/city/')
def showCities():
    cities = session.query(City).order_by(asc(City.name))
    if 'username' not in login_session:
        return render_template('publiccities.html', cities=cities)
    else:
        return render_template('cities.html', cities=cities)

# Create a new city
@app.route('/city/new/', methods=['GET', 'POST'])
def newCity():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCity = City(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCity)
        flash('New City %s Successfully Created' % newCity.name)
        session.commit()
        return redirect(url_for('showCities'))
    else:
        return render_template('newCity.html')

# Edit a city
@app.route('/city/<int:city_id>/edit/', methods=['GET', 'POST'])
def editCity(city_id):
    editedCity = session.query(
        City).filter_by(id=city_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedCity.user_id != login_session['user_id']:
        script = "<script>function myFunction() {alert('You are not "
        script += "authorized to edit this city. Please create your own "
        script += "city in order to edit."
        script += "');}</script><body onload='myFunction()'>"
        return script
    if request.method == 'POST':
        if request.form['name']:
            editedCity.name = request.form['name']
            flash('City Successfully Edited %s' % editedCity.name)
            return redirect(url_for('showCities'))
    else:
        return render_template('editCity.html', city=editedCity)


# Delete a city
@app.route('/city/<int:city_id>/delete/', methods=['GET', 'POST'])
def deleteCity(city_id):
    cityToDelete = session.query(
        City).filter_by(id=city_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if cityToDelete.user_id != login_session['user_id']:
        script = "<script>function myFunction() {alert('You are not "
        script += "authorized to delete this city. Please create your own "
        script += "city in order to delete."
        script += "');}</script><body onload='myFunction()'>"
        return script
    if request.method == 'POST':
        session.delete(cityToDelete)
        flash('%s Successfully Deleted' % cityToDelete.name)
        session.commit()
        return redirect(url_for('showCities', city_id=city_id))
    else:
        return render_template('deleteCity.html', city=cityToDelete)


# Show restaurants
@app.route('/city/<int:city_id>/')
@app.route('/city/<int:city_id>/restaurants/')
def showRestaurants(city_id):
    city = session.query(City).filter_by(id=city_id).one()
    creator = getUserInfo(city.user_id)
    items = session.query(RestaurantItem).filter_by(
        city_id=city_id).all()
    if 'username' not in login_session or creator.id != login_session[
            'user_id']:
        return render_template(
            'publicrestaurants.html', items=items, city=city, creator=creator)
    else:
        return render_template(
            'restaurants.html', items=items, city=city, creator=creator)


# Create restaurant
@app.route('/city/<int:city_id>/restaurants/new/', methods=['GET', 'POST'])
def newRestaurantItem(city_id):
    if 'username' not in login_session:
        return redirect('/login')
    city = session.query(City).filter_by(id=city_id).one()
    if login_session['user_id'] != city.user_id:
        script = "<script>function myFunction() {alert('You are not "
        script += "authorized to add restaurant items to this city. "
        script += "Please create your own city in order to add items."
        script += "');}</script><body onload='myFunction()'>"
        return script
    if request.method == 'POST':
        newItem = RestaurantItem(
            name=request.form['name'], description=request.form['description'],
            address=request.form['address'], rating=request.form['rating'],
            city_id=city_id, user_id=city.user_id)
        session.add(newItem)
        session.commit()
        flash('New Restaurant %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showRestaurants', city_id=city_id))
    else:
        return render_template('newrestaurantitem.html', city_id=city_id)


# Edit restaurant
@app.route(
    '/city/<int:city_id>/restaurants/<int:restaurant_id>/edit',
    methods=['GET', 'POST'])
def editRestaurantItem(city_id, restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(RestaurantItem).filter_by(
        id=restaurant_id).one()

    city = session.query(City).filter_by(id=city_id).one()
    if login_session['user_id'] != city.user_id:
        script = "<script>function myFunction() {alert('You are not "
        script += "authorized to edit restaurant items to this restaurant. "
        script += "Please create your own restaurant in order to edit items.'"
        script += ");}</script><body onload='myFunction()'>"
        return script
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['address']:
            editedItem.address = request.form['address']
        if request.form['rating']:
            editedItem.rating = request.form['rating']
        session.add(editedItem)
        session.commit()
        flash('Restaurant Item Successfully Edited')
        return redirect(url_for('showRestaurants', city_id=city_id))
    else:
        return render_template(
            'editrestaurantitem.html', city_id=city_id,
            restaurant_id=restaurant_id, item=editedItem)


# Delete a restaurant
@app.route(
    '/city/<int:city_id>/restaurants/<int:restaurant_id>/delete',
    methods=['GET', 'POST'])
def deleteRestaurantItem(city_id, restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    city = session.query(City).filter_by(id=city_id).one()
    iToDelete = session.query(RestaurantItem).filter_by(id=restaurant_id).one()
    if login_session['user_id'] != city.user_id:
        script = "<script>function myFunction() {alert('You are not "
        script += "authorized to delete restaurant items to this restaurant. "
        script += "Please create your own restaurant in order to delete "
        script += "items.');}</script><body onload='myFunction()'>"
        return script
    if request.method == 'POST':
        session.delete(iToDelete)
        session.commit()
        flash('Restaurant Item Successfully Deleted')
        return redirect(url_for('showRestaurants', city_id=city_id))
    else:
        render_template(
            'deleterestaurantitem.html', city_id=city_id,
            restaurant_id=restaurant_id, item=iToDelete)

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCities'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCities'))


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.debug = True
	app.run(host='0.0.0.0')
