from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash #I used Werkzeug from my Python environment to generate a
#password hash and check password for an added robust solution.
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.config['SECRET_KEY'] = 'neige_virgilio_'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///property_database.db' # I could use:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # this configuration of the code since I am don't really use
#SQLAlchemy but it will erase all the code a soon as I start running it.

db = SQLAlchemy(app)

class Property(db.Model): # this database shows the tenants the information they need in order to register interest in a certain property
    id = db.Column(db.Integer, primary_key=True) #classified id as an interger since there can only be numbers inserted
    #it is also a primary key as the columns each contains values that are unique to each other in SqlAlchemy/SQL/sqliter
# because each prospective tenants information will be unique to them.
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True) #I chose Boolean because it obviously only gives you two options "yes" or "no"
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=False)
    agent = db.relationship('Agent', backref=db.backref('properties', lazy=True))

    def __repr__(self):
        return f"<Property {self.name}>"

class Agent(db.Model): # this is where the agents log into their admin accounts and all information gets stored on the database.
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Agent {self.name}>"

class Tenant(db.Model):# this is the information the tenants need to give when registering interest and their will also be saved on the database
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    property = db.relationship('Property', backref=db.backref('tenants', lazy=True))

    def __repr__(self):
        return f"<Tenant {self.name}>"

db.create_all() #Challenge: this line brings up no errors or warnings in my project, but it does throw an exception when I try to run
# when I the solution, I have come to the possible conclusions that the Visual Studio IDE I am using is either not
#compatable with some of my code, I do have the current version I believe but it's not picking up this specific line of code

# Email Configuration (Replace with your email credentials)
EMAIL_HOST = 'smtp.gmail.com'  # Or your email provider's server
EMAIL_PORT = 587
EMAIL_USER = 'neigevirgilio@gmail.com'
EMAIL_PASSWORD = 'Iwaslikeok97!'

def send_email(to_email, subject, message):
    msg = MIMEText(message, 'plain') #MIMEText is a class I created for the emails in order to recieve major type texts
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASSWORD)
        smtp.sendmail(EMAIL_USER, to_email, msg.as_string())

# Routes
@app.route('/')
def index():
    properties = Property.query.filter_by(available=True).all()
    return render_template('index.html', properties=properties)

@app.route('/property/<property_id>')
def property_details(property_id):
    property = Property.query.get_or_404(property_id)
    return render_template('property_details.html', property=property)

@app.route('/register_interest/<property_id>', methods=['POST'])
def register_interest(property_id):
    property = Property.query.get_or_404(property_id)
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    tenant = Tenant(name=name, email=email, phone=phone, property_id=property_id)
    db.session.add(tenant)
    db.session.commit()

    send_email(property.agent.email, 'New Tenant Interest',
               f'A new tenant, {name}, is interested in property: {property.name}. Their email is: {email}')

    return render_template('success.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        agent = Agent.query.filter_by(email=email).first()
        if agent and check_password_hash(agent.password, password):
            session['agent_id'] = agent.id
            return redirect(url_for('agent_dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/agent_dashboard')
def agent_dashboard():
    if 'agent_id' in session:
        agent = Agent.query.get(session['agent_id'])
        tenants = []
        for property in agent.properties:
            tenants.extend(property.tenants)
        return render_template('agent_dashboard.html', agent=agent, tenants=tenants)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('agent_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
