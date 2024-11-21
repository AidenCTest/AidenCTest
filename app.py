# import Flask class definition from library
from flask import Flask, request, jsonify
# SQLAlchemy is an Object Relational Mapper allowing decoupling of db operations
from flask_sqlalchemy import SQLAlchemy
# Marshmallow is an object serialization/deserialization library
from flask_marshmallow import Marshmallow

import datetime


# Instantiate the Flask app and setup configurations
app = Flask(__name__)

# SQLAlchemy configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///observations.db'  # Database file
app.config['SQLALCHEMY_ECHO'] = True  # Echo SQL queries (for debugging)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable track modifications

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Define the Observation model
class Observation(db.Model):
    ObservationID = db.Column(db.Integer, primary_key=True)  # Auto-increment primary key
    Date = db.Column(db.Date, nullable=False)
    Time = db.Column(db.Time, nullable=False)
    TimeZoneOffset = db.Column(db.Integer, nullable=True)
    Coordinates = db.Column(db.String(255), nullable=True)
    WaterTemp = db.Column(db.Float, nullable=True)
    AirTemp = db.Column(db.Float, nullable=True)
    Humidity = db.Column(db.Float, nullable=True)
    WindSpeed = db.Column(db.Float, nullable=True)
    WindDirection = db.Column(db.Float, nullable=True)
    Precipitation = db.Column(db.Float, nullable=True)
    Haze = db.Column(db.Float, nullable=True)
    Becquerel = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<Observation {self.ObservationID}>'

# Marshmallow schema for serialization
class ObservationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Observation
        load_instance = True
        sqla_session = db.session

# Instantiate the schema
observation_schema = ObservationSchema()
observations_schema = ObservationSchema(many=True)

# Ensure to use app context for any non-request-based operations (like background tasks)
def perform_db_task():
    """Perform a database task, e.g., cleanup, outside of a request"""
    with app.app_context():  # Push the app context
        # Any database operation that needs context goes here
        observations = Observation.query.all()
        print(observations)  # For example, print all observations
        # Perform any other database tasks you need

# Endpoint to view all observations
@app.route('/observations/get-all-observations', methods=['GET'])
def get_all_observations():
    """Endpoint used to view all observations from the DB"""
    observations = Observation.query.all()
    return observations_schema.jsonify(observations)

# Endpoint to view a single observation by ID using route parameter
@app.route('/observations/get-one-observation/<int:ObservationID>', methods=['GET'])
def get_one_observation_route(ObservationID):
    """Endpoint that queries a specific observation by ObservationID from the DB"""
    observation = Observation.query.filter_by(ObservationID=ObservationID).first()
    if observation:
        return observation_schema.jsonify(observation)
    else:
        return jsonify({"message": "Observation not found"}), 404

# Endpoint to view a single observation by ID using query parameter
@app.route('/observations/get-one-observation', methods=['GET'])
def get_one_observation_query():
    """Endpoint uses query parameters to query an observation by ObservationID"""
    ObservationID = request.args.get('ObservationID')
    observation = Observation.query.filter_by(ObservationID=ObservationID).first()
    if observation:
        return observation_schema.jsonify(observation)
    else:
        return jsonify({"message": "Observation not found"}), 404

# Endpoint to add a new observation via JSON data
@app.route('/observations/add-observation-json', methods=['POST'])
def observation_add_json():
    json_data = request.get_json()

    try:
        # Convert Date and Time into proper datetime objects
        date = datetime.datetime.strptime(json_data['Date'], '%Y-%m-%d').date()
        time = datetime.datetime.strptime(json_data['Time'], '%H:%M:%S').time()

        new_observation = Observation(
            Date=date,
            Time=time,
            TimeZoneOffset=json_data.get('TimeZoneOffset'),
            Coordinates=json_data.get('Coordinates'),
            WaterTemp=json_data.get('WaterTemp'),
            AirTemp=json_data.get('AirTemp'),
            Humidity=json_data.get('Humidity'),
            WindSpeed=json_data.get('WindSpeed'),
            WindDirection=json_data.get('WindDirection'),
            Precipitation=json_data.get('Precipitation'),
            Haze=json_data.get('Haze'),
            Becquerel=json_data.get('Becquerel')
        )

        db.session.add(new_observation)
        db.session.commit()

        return observation_schema.jsonify(new_observation), 201

    except KeyError as e:
        return jsonify({"message": f"Missing field: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"message": f"Error adding observation: {str(e)}"}), 500

# Endpoint to modify an existing observation (PUT request)
@app.route('/observations/modify-observation-json/<int:ObservationID>', methods=['PUT'])
def modify_observation(ObservationID):
    observation = Observation.query.filter_by(ObservationID=ObservationID).first()
    if observation:
        json_data = request.get_json()

        # Convert Date and Time into proper datetime objects if provided
        if 'Date' in json_data:
            observation.Date = datetime.datetime.strptime(json_data['Date'], '%Y-%m-%d').date()
        if 'Time' in json_data:
            observation.Time = datetime.datetime.strptime(json_data['Time'], '%H:%M:%S').time()

        # Update other fields if they are provided in the JSON
        observation.TimeZoneOffset = json_data.get('TimeZoneOffset', observation.TimeZoneOffset)
        observation.Coordinates = json_data.get('Coordinates', observation.Coordinates)
        observation.WaterTemp = json_data.get('WaterTemp', observation.WaterTemp)
        observation.AirTemp = json_data.get('AirTemp', observation.AirTemp)
        observation.Humidity = json_data.get('Humidity', observation.Humidity)
        observation.WindSpeed = json_data.get('WindSpeed', observation.WindSpeed)
        observation.WindDirection = json_data.get('WindDirection', observation.WindDirection)
        observation.Precipitation = json_data.get('Precipitation', observation.Precipitation)
        observation.Haze = json_data.get('Haze', observation.Haze)
        observation.Becquerel = json_data.get('Becquerel', observation.Becquerel)

        db.session.commit()

        return observation_schema.jsonify(observation)
    else:
        return jsonify({"message": "Observation not found"}), 404

# Endpoint to delete an observation by ID
@app.route('/observations/delete-observation/<int:ObservationID>', methods=['DELETE'])
def delete_observation(ObservationID):
    observation = Observation.query.filter_by(ObservationID=ObservationID).first()
    if observation:
        db.session.delete(observation)
        db.session.commit()
        return jsonify({"message": f"Observation {ObservationID} deleted successfully"}), 200
    else:
        return jsonify({"message": "Observation not found"}), 404

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
