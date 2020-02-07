#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from datetime import datetime
import pytz
from sqlalchemy import desc
from models import Venue,Artist,Show


utc=pytz.UTC

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


########################################################################################################################################

def format_datetime(value, format='full'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ------------------------------------------------------------------------------------------------------------------------------

@app.route('/venues')
def venues():
  data=[]
  venues=Venue.query.distinct('city','state').all()
  for venue in venues:
    ven=Venue.query.filter_by(city=venue.city).all()
    num_upcomming_shows=Venue.query.filter_by(city=venue.city,state=venue.state)\
    .join(Show).filter(Show.start_time > datetime.utcnow().replace(tzinfo=pytz.UTC)).count()
    mydata={
      "city":venue.city,
      "state":venue.state,
      "venues":ven,
      "num_upcomming_shows":num_upcomming_shows
    }
    data.append(mydata)
  return render_template('pages/venues.html', areas=data)


#  Search Venue
#  --------------------------------------------------------------------------------------------------------------------------------
@app.route('/venues/search', methods=['POST'])
def search_venues():
  search = "%{}%".format(request.form.get('search_term', ''))
  venues = Venue.query.filter(Venue.name.ilike(search)).all()
  count=len(venues)
  response={
    "count": count,
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


#  GET on VENUE
#  ------------------------------------------------------------------------------------------------------------------------------------
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  myvenue = Venue.query.get(venue_id)
  if(len(Venue.query.filter_by(id=venue_id).all())!=0):
    past = []
    for show in Show.query.filter(Show.venues_id==venue_id).order_by(desc(Show.start_time)).limit(10):
      if show.start_time < utc.localize(datetime.now()):
        past.append({
          "artist_id":show.artists_id,
          "artist_name":Artist.query.filter(Artist.id==show.artists_id).first().name,
          "artist_image_link":Artist.query.filter(Artist.id==show.artists_id).first().image_link,
          "start_time":show.start_time.strftime("%c")
        })
    upcoming = []
    for show in Show.query.filter(Show.venues_id==venue_id).order_by(desc(Show.start_time)).limit(10):
      if show.start_time > utc.localize(datetime.now()):
        upcoming.append({
        "artist_id":show.artists_id,
        "artist_name":Artist.query.filter(Artist.id==show.artists_id).first().name,
        "artist_image_link":Artist.query.filter(Artist.id==show.artists_id).first().image_link,
        "start_time":show.start_time.strftime("%c")
        })
    
    data={
      "id": myvenue.id,
      "name": myvenue.name,
      "genres": myvenue.genres,
      "address": myvenue.address,
      "city": myvenue.city,
      "state": myvenue.state,
      "phone": myvenue.phone,
      "website": myvenue.website,
      "facebook_link": myvenue.facebook_link,
      "seeking_talent": myvenue.seeking_talent,
      "seeking_description": myvenue.seeking_description,
      "image_link": myvenue.image_link,
      "past_shows":past,
      "upcoming_shows":upcoming,
      "past_shows_count": len(past),
      "upcoming_shows_count": len(upcoming)
    }
    data = list(filter(lambda d: d['id'] == venue_id, [data]))[0]
    return render_template('pages/show_venue.html',past_shows=past,upcoming_shows=upcoming,venue=data)
  else:
    flash('Venue does not exist')
    return redirect(url_for('venues'))


#  Create Venue GET
#  -----------------------------------------------------------------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


#  Create Venue POST
#  -------------------------------------------------------------------------------------------------------------------------
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    name = request.form.get('name')
    city=  request.form.get('city')
    state=  request.form.get('state')
    address=  request.form.get('address')
    phone=  request.form.get('phone')
    genres= request.form.getlist('genres')
    facebook_link=  request.form.get('facebook_link')
    image_link=request.form.get('image_link')
    seeking_description=request.form.get('seeking_description')
    website=request.form.get('website')
    #seeking_talent=request.form.get('seeking_talent')
    venue = Venue(name=name,city=city,state=state,address=address,phone=phone,image_link=image_link,facebook_link=facebook_link,genres=genres,website=website,seeking_talent=True,seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except: 
    db.session.rollback()
    flash('An error occurred. Venue '+ request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  DELETE Venue
#  ------------------------------------------------------------------------------------------------------------------------------

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully deleted!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue '+ request.form['name'] + ' can not be deleted.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Artists
#  ---------------------------------------------------------------------------------------------------------------------------------
@app.route('/artists')
def artists():
  data=Artist.query.all()
  return render_template('pages/artists.html', artists=data)

#  Search artist
#  -----------------------------------------------------------------------------------------------------------------------------------
@app.route('/artists/search', methods=['POST'])
def search_artists():
  search = "%{}%".format(request.form.get('search_term', ''))
  artists = Artist.query.filter(Artist.name.ilike(search)).all()
  count=len(artists)
  response={
    "count": count,
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

#  GET one  artist
#  ---------------------------------------------------------------------------------------------------------------------------------------
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  myartist = Artist.query.get(artist_id)
  if(len(Artist.query.filter_by(id=artist_id).all())!=0):
    past = []
    for show in Show.query.filter(Show.artists_id==artist_id).order_by(desc(Show.start_time)).limit(10):
      if show.start_time < utc.localize(datetime.now()):
        past.append({
          "venue_id":show.venues_id,
          "venue_name":Venue.query.filter(Venue.id==show.venues_id).first().name,
          "venue_image_link":Venue.query.filter(Venue.id==show.venues_id).first().image_link,
          "start_time":show.start_time.strftime("%c")
          
        })  
    upcoming = []
    for show in Show.query.filter(Show.artists_id==artist_id).order_by(desc(Show.start_time)).limit(10):
      if show.start_time > utc.localize(datetime.now()):
        upcoming.append({
          "venue_id":show.venues_id,
          "venue_name":Venue.query.filter(Venue.id==show.venues_id).first().name,
          "venue_image_link":Venue.query.filter(Venue.id==show.venues_id).first().image_link,
          "start_time":show.start_time.strftime("%c")
        })

    data={
      "id": myartist.id,
      "name": myartist.name,
      "genres": myartist.genres,
      "city": myartist.city,
      "state": myartist.state,
      "phone": myartist.phone,
      "website": myartist.website,
      "facebook_link": myartist.facebook_link,
      "seeking_venue": myartist.seeking_venue,
      "seeking_description": myartist.seeking_description,
      "image_link": myartist.image_link,
      "past_shows": past,
      "upcoming_shows": upcoming,
      "past_shows_count": len(past),
      "upcoming_shows_count": len(upcoming)
    }
    data = list(filter(lambda d: d['id'] == artist_id, [data]))[0]
    return render_template('pages/show_artist.html',past_shows=past,upcoming_shows=upcoming,artist=data)
  else:
    flash('Artist does not exist')
    return redirect(url_for('artists'))
   

#  Edit GET artist
#  ----------------------------------------------------------------------------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist=Artist.query.get(artist_id)
  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.facebook_link.data = artist.facebook_link
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link
  form.website.data = artist.website
  #form.seeking_venue=artist.seeking_venue
   
  return render_template('forms/edit_artist.html', form=form, artist=artist)


#  Edit POST artist
#  ---------------------------------------------------------------------------------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    artist = Artist.query.get(artist_id)
    artist.name=request.form.get('name')
    artist.city=request.form.get('city')
    artist.state=request.form.get('state')
    artist.phone=request.form.get('phone')
    artist.genres=request.form.getlist('genres')
    artist.facebook_link= request.form.get('facebook_link')
    artist.seeking_description=request.form.get('seeking_description')
    artist.image_link=request.form.get('image_link')
    artist.website=request.form.get('website')
    #artist.seeking_venue=request.form.get('seeking_venue')
    db.session.commit()
    flash('Artist ' + artist.name + ' has been successfully updated !')
  except:
    db.session.rollback()
    flash('An error occurred. Artist '+ artist.name + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))


#  EDIT GET Venue
#  ----------------------------------------------------------------------------------------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue=Venue.query.get(venue_id)
  form.name.data = venue.name
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.facebook_link.data = venue.facebook_link
  #form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link
  form.website.data = venue.website
  form.facebook_link.data = venue.facebook_link
  return render_template('forms/edit_venue.html', form=form, venue=venue)


#  Edit POST VENUE
#  ----------------------------------------------------------------------------------------------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    venue.name=request.form.get('name')
    venue.city=request.form.get('city')
    venue.state=request.form.get('state')
    venue.address=request.form.get('address')
    venue.phone=request.form.get('phone')
    venue.genres=request.form.getlist('genres')
    venue.facebook_link= request.form.get('facebook_link')
    venue.seeking_description=request.form.get('seeking_description')
    venue.image_link=request.form.get('image_link')
    venue.website=request.form.get('website')
    #venue.seeking_talent=request.form.get('seeking_talent')
    db.session.commit()
    flash('Venue ' + venue.name + ' has been successfully updated !')
  except:
    db.session.rollback()
    flash('An error occurred. Venue '+ venue.name + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist GET
#  --------------------------------------------------------------------------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


#  Create artist POST
#  -------------------------------------------------------------------------------------------------------------------------------------
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    name = request.form.get('name')
    city=  request.form.get('city')
    state=  request.form.get('state')
    phone=  request.form.get('phone')
    genres= request.form.getlist('genres')
    facebook_link=  request.form.get('facebook_link')
    image_link=request.form.get('image_link')
    website= request.form.get('website')
    seeking_description=request.form.get('seeking_description')
    #seeking_venue=request.form.get('seeking_venue')
    artist = Artist(name=name,city=city,state=state,phone=phone,genres=genres,image_link=image_link,facebook_link=facebook_link,website=website,seeking_venue=True,seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except: 
    db.session.rollback()
    flash('An error occurred. Artist '+ request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows all venue
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  data=[]
  mydatas=db.session.query(Venue,Show,Artist).join(Show,Venue.id==Show.venues_id).join(Artist,Show.artists_id==Artist.id).filter(Show.start_time > datetime.now()).all()
  for mydata in mydatas:
    d=mydata.Show.start_time
    mydata={
      "venue_id":mydata.Venue.id,
      "venue_name": mydata.Venue.name,
      "artist_id": mydata.Artist.id,
      "artist_name":mydata.Artist.name,
      "artist_image_link": mydata.Artist.image_link,
      "start_time": d.strftime("%c")
    }
    data.append(mydata)
  return render_template('pages/shows.html', shows=data)

#  Create Show GET
#  ----------------------------------------------------------------
@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

#  Create Show POST
#  ----------------------------------------------------------------
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm()
  try:
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time=request.form.get('start_time')
    exit_show=Show.query.filter_by(venues_id=venue_id, artists_id=artist_id,start_time=start_time).all()
    if len(exit_show)==0:
      show = Show(venues_id=venue_id,artists_id=artist_id,start_time=start_time)
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')
    else:
      flash('This artist has already another show which start at the same time. Please change date and hour of  show')
      return render_template('forms/new_show.html', form=form)
  except: 
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
