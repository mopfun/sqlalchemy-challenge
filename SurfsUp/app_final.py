# Import the dependencies.
import numpy as np
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save reference to the table
measurement = Base.classes.measurement #measurements class
station = Base.classes.station #stations class


# Create our session (link) from Python to the DB
session = Session(bind=engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

#Homepage Route
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/Percipitation - last 12 mo of percipitaion data<br/>"
        f"/api/v1.0/Stations - list of stations<br/>"
        f"/api/v1.0/TOBS - temp observations for the most active stations<br/>"
        f"/api/v1.0/&lt;start&gt; - TMIN, TAVG, TMAX from start date<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt; - TMIN, TAVG, TMAX from start and end dates<br/>"
    )

#Percipitation Route
@app.route("/api/v1.0/Percipitation")
def Percipitation():
    """Percipitation Analysis of last 12 months."""
    session = Session(engine)

    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    query_date = most_recent_date - dt.timedelta(days=365)
    
    results = session.query(measurement.date, measurement.prcp).filter(measurement.date>=query_date).all()
     
    precipitation_data = session.query(measurement.date, measurement.prcp).\
        filter(measurement.date >= query_date).\
        order_by(measurement.date).all()

    session.close()  # Close session

    prcp_dict = {date: prcp for date, prcp in results}
    
    return jsonify(prcp_dict)

#Stations Route
@app.route("/api/v1.0/Stations")
def Stations ():
    """List of Stations."""
    session = Session(engine)

    stations = session.query(station.station).all()
    session.close()

    stations_list = list(np.ravel(stations))
    return jsonify(stations_list)

#TOBS Route
@app.route("/api/v1.0/TOBS")
def TOBS ():
    """Temp Observations for The Most Active Stations."""
    session = Session(engine)
    most_active_stations = session.query(
        measurement.station,func.count(measurement.station)).\
        group_by(measurement.station).\
        order_by(func.count(measurement.station).desc()).first()[0]
    
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    query_date = most_recent_date - dt.timedelta(days=365)

    past_12_mo = session.query(measurement.date, measurement.tobs).\
        filter(measurement.station == most_active_stations).\
        filter(measurement.date >= query_date).all()

    session.close()

    temp_list = list(np.ravel(past_12_mo))
    return jsonify(temp_list)

#Start Route
@app.route("/api/v1.0/<tart>")
def Temp_Start_Analysis (start=None):
    """TMIN, TAVG, TMAX for dates greater than or equal to the start date."""
    start = start.strip()  # Removes any extra spaces
    try:
        dt.datetime.strptime(start, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid start date format. Use YYYY-MM-DD."}), 400
    
    session = Session(engine)

    temp_stats = session.query(
        func.min(measurement.tobs),
        func.max(measurement.tobs),
        func.avg(measurement.tobs)
    ).filter(measurement.date >= start).all()
    
    session.close()

    temp_stats_list = list(np.ravel(temp_stats))
    return jsonify(temp_stats_list)

#Start/End Route
@app.route("/api/v1.0/<start>/<end>")
def temp_range(start=None, end=None):
    """TMIN, TAVG, TMAX for the dates greater than or equal to the start date (or between start and end)."""
    start = start.strip()
    end = end.strip()
    
    # Date validation using try-except
    try:
        dt.datetime.strptime(start, "%Y-%m-%d")
        dt.datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    
    session = Session(engine)

    temp_stats = session.query(
        func.min(measurement.tobs),
        func.avg(measurement.tobs),
        func.max(measurement.tobs)
    ).filter(measurement.date >= start).\
        filter(measurement.date <= end).all()

    session.close()

    temp_stats_list = list(np.ravel(temp_stats))
    return jsonify(temp_stats_list)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)