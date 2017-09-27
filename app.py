#!/usr/bin/python2.7
from flask import Flask, render_template,request, url_for, redirect, session
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import  check_password_hash
from flask_login import LoginManager, login_required, login_user,UserMixin, logout_user,current_user
from sqlalchemy import text
import atexit
from apscheduler.scheduler import Scheduler
import datetime


app = Flask(__name__)
cron = Scheduler(daemon=True)
cron.start()


app.config['SECRET_KEY'] = ';Y8m4e#PUP\qQR]+"`ZAM(&td{8utWN?CtHXg6X(-z!$XP4?(t)~g4Kk9xgr8}ZaH]eGx(:uvNE}GVp;'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LePzS8UAAAAADoA_QPfGVUArvWnA0oF9eZi7-L7'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lf3yS8UAAAAAExePlZihuoFhiZIcZOKWskui3sd'
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///leave.db"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
user_name={'jdas':'Jyoti','bdas':'Byomkesh','cjog':'Chinmay','skupwadde':'Swaapnesh','kahire':'Kapil',
           'ashinde':'Abhijit','dpatil':'Dinesh'}

class Users(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True,nullable=False)
    password = db.Column(db.String(80),nullable=False)
    balance = db.Column(db.Integer)
    leaves = db.relationship('LeaveDetail', backref='user', lazy='dynamic')


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class LeaveDetail(db.Model):
    __tablename__ = 'leavedetail'
    id = db.Column(db.Integer, primary_key=True)
    sdate = db.Column(db.DateTime,nullable=False)
    edate = db.Column(db.DateTime,nullable=False)
    days = db.Column(db.Integer,nullable=False)
    a_time = db.Column(db.DateTime,nullable=False)
    reason = db.Column(db.String(200))
    active = db.Column(db.Integer,nullable=False)
    usr_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    recaptcha = RecaptchaField()


@app.route('/')
@app.route('/login/', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit() :
        db_usr = Users.query.filter_by(username=form.username.data).first()
        if db_usr:
            if check_password_hash(db_usr.password,form.password.data):
                login_user(db_usr, remember=True)
                session['username'] = form.username.data
                session['login_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                session['user_id'] = current_user.get_id()
                return render_template('welcome.html', name=user_name[session['username']])
            else:
                return render_template('login.html',form=form, error='Password is not matching...')

    return render_template('login.html', form=form)

@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html',name=user_name[session['username']])

@app.route('/plan/', methods=['GET','POST'])
@login_required
def plan():
    balance = Users.query.filter_by(id=current_user.get_id()).first()
    dbbalance = balance.balance
    if request.method == 'POST':
        if request.form['sdate'] > request.form['edate'] :
            return render_template('plan.html', error='Start date is greater than End date')
        sdate = datetime.datetime.strptime(str(request.form['sdate']),'%Y-%m-%d')
        edate = datetime.datetime.strptime(str(request.form['edate']),'%Y-%m-%d')
        days = int(request.form['days'])
        ctime=datetime.datetime.now()
        if int(days) <= dbbalance:
            updated_balance = dbbalance - int(days)
            balance.balance = updated_balance
            leave = LeaveDetail(sdate=sdate, edate=edate,days=days,a_time=ctime,reason=request.form['reason'],active=1,
                            user = current_user )
            db.session.add(leave)
            db.session.commit()
            request.form = {}
            return render_template('plan.html',message='Leave applied from {} to {} for {} days'.format(sdate,edate,
                                                                                                        days))
        else:
            balance = balance.balance
            return render_template('plan.html', error='You have only {} no of leaves'.format(balance))

    else:
        return render_template('plan.html',message='You have {} nos. of leave in your bucket!!!'.format(dbbalance))

@app.route('/cancel/',methods=['GET','POST'])
@login_required
def cancel():
    results = db.engine.execute(text("select username,sdate,edate,reason from users join leavedetail on users.id = "
                                     "leavedetail.usr_id where users.id = {} and leavedetail.active = 1".format(
        current_user.get_id())))
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    for result in results:
        if today <= result[1]:
            return render_template('cancel.html', list=result)
    else:
        return render_template('cancel.html', message="Wow!! You don't have any leave in past....")
@app.route('/cancel/<string:daterange>')
def soft_delete(daterange):
    sdate,edate = daterange.split('=')
    print sdate,edate
    d_query='update leavedetail set active = 0 where sdate=\'{}\' and edate=\'{}\' and usr_id = {}'.format(sdate+' '
                                                                                                         '00:00:00.000000',edate+' 00:00:00.000000',
                                                                                                   session['user_id'])
    results = db.engine.execute(text(d_query))
    if results:
        db.session.commit()
    else:
        return render_template('cancel.html', error='Some problem with DB....')

    return redirect('cancel')

@app.route('/comp-off/')
@login_required
def compoff():
    return render_template('compoff.html')


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',error=e)

@cron.cron_schedule(day='1')
def job_function():
    for row in Users.query.all():
        row.balance = row.balance + 2
        db.session.commit()


atexit.register(lambda: cron.shutdown(wait=False))

if __name__ == "__main__":
    app.run(debug=True)


