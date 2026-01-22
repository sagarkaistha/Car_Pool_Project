from flask import Flask,render_template,request,session,redirect,url_for,flash
from flask_mysqldb import MySQL
from flask_socketio import join_room, leave_room, send, SocketIO
from string import ascii_uppercase
from flask_session import Session
import random

app = Flask(__name__)
app.secret_key = "supers secret key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
socketio = SocketIO(app)

rooms = {}

app.config['MYSQL_HOST']= "localhost"
app.config['MYSQL_USER']= "root"
app.config['MYSQL_PASSWORD']= "mysql@123"
app.config['MYSQL_DB']= "campuspool"
mysql=MySQL(app)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('home.html')


@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email=request.form['email']
        number=request.form['number']
        if len(number) != 10:
            return render_template('errors.html',error="Number is wrong")
        password=request.form['password']
        cpassword=request.form['cpassword']
        cur=mysql.connection.cursor()
        cur.execute('SELECT * FROM user WHERE email = %s', (email,  ))
        account = cur.fetchone()
        if account:
            return "Account Exists"   
        else:
            if(password==cpassword):
                curs=mysql.connection.cursor()
                curs.execute("INSERT INTO user (name,email,number,password) VALUES (%s,%s,%s,MD5(%s))",(name,email,number,password))
                mysql.connection.commit()
                cur.close()
                return render_template('home.html')
            else:
                return render_template('errors.html',error="Passwords dont match")
    return render_template('signup.html')


@app.route('/user',methods=['GET','POST'])
def user():
    return render_template('user.html')


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password=request.form['password']
        cur=mysql.connection.cursor()
        cur.execute('SELECT * FROM user WHERE email = %s AND password = MD5(%s)', (email, password))
        account = cur.fetchone()
                # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in othr routes
            session[0] = True
            session[1] = str(account[0])
            session[2] = account[1]
            session[3] = account[2]
            session[4] = str(account[4])
            # Redirect to home page
            return render_template('user.html')
        else:
            # Account doesnt exist or username/password incorrect
            return render_template('login.html')
    return render_template('login.html')


@app.route('/book',methods=['GET','POST'])
def book():  
    if request.method == 'POST':
        date = request.form['date']
        time=request.form['time']
        passenger=request.form['passenger']
        cur=mysql.connection.cursor()
        session[5]=passenger
        cur.execute('SELECT * FROM booking WHERE date = %s and passengers >=%s and time =%s and approve<2', (date,passenger,time))
        account = cur.fetchall()  
        if len(account) == 0:
            return render_template('error.html',)
        else:
            return render_template('result.html', data=account,)
    return render_template('book.html')


@app.route('/bookings',methods=['GET','POST'])
def bookings():  
    if session :
        return render_template('user.html')
    else:
        return render_template('login.html')


@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        date = request.form['date']
        passengers=request.form['passengers']
        destination=request.form['destination']
        time=request.form['time']
        s_id= session[1]
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO booking (s_id,date,time,passengers,destination) VALUES (%s,%s,%s,%s,%s)",(s_id,date,time,passengers,destination))
        mysql.connection.commit()
        cur.close()
        return render_template('user.html',data=passengers)
    return render_template('register.html')


@app.route('/result',methods=['GET','POST'])
def result():  
    if request.method == 'POST':
        id=request.form['id']
        time=request.form['time']
        cur=mysql.connection.cursor()
        cur.execute('SELECT * FROM user WHERE id = %s',(id,))
        account = cur.fetchone() 
        cur=mysql.connection.cursor()
        cur.execute('SELECT * FROM booking WHERE s_id = %s AND time =%s and approve<2',(id,time))
        accounts = cur.fetchone()    
        return render_template('approve.html', data=account,datas=accounts)
    return render_template('result.html')


@app.route('/approve',methods=['GET','POST'])
def approve():  
    if request.method == 'POST':
        id=request.form['id']
        id1=session[1]
        time=request.form['time']
        date=request.form['date']
        passenger=session[5]
        destination=request.form['destination']
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO request (r_id,s_id,date,time,destination,passenger) VALUES (%s,%s,%s,%s,%s,%s)",(id,id1,date,time,destination,passenger))
        mysql.connection.commit()
        cur.close()   
        return render_template('user.html')
    return render_template('approve.html')


@app.route('/requests',methods=['GET','POST'])
def requests():
    id=session[1]
    cur=mysql.connection.cursor()
    cur.execute('SELECT * FROM request WHERE r_id=%s',(id,))
    accounts = cur.fetchall()
    mysql.connection.commit()
    cur.close()
    return render_template('requests.html',data=accounts)


@app.route('/confirm',methods=['GET','POST'])
def confirm():
    if request.method == 'POST':
        id=request.form['id']
        ids=request.form['name']
        cur=mysql.connection.cursor()
        cur.execute('SELECT * FROM user WHERE id=%s',(id,))
        accounts = cur.fetchone()
        mysql.connection.commit()
        cur.close()
        cur=mysql.connection.cursor()
        cur.execute('SELECT * FROM request WHERE id=%s and approve=0',(ids,))
        account = cur.fetchone()
        mysql.connection.commit()
        cur.close()
        return render_template('confirm.html',data=accounts,datas=account) 


@app.route("/chatreq", methods=["POST", "GET"])
def chatreq():
    id=session[1]
    cur=mysql.connection.cursor()
    cur.execute('SELECT * FROM chat WHERE id1=%s', (id,))
    account = cur.fetchall()
    return render_template("chatreq.html",data=account)


@app.route("/chathome", methods=["POST", "GET"])
def chathome():
    if request.method == "POST":
        name = session[1]
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return 'fail1'
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join != False and not code:
            return 'fail2'
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            id=request.form.get("id")
            cur=mysql.connection.cursor()
            cur.execute('SELECT * FROM request WHERE id=%s',(id,))
            account = cur.fetchone()
            ids=account[2]
            nam=session[2]
            idz=account[0]
            cur=mysql.connection.cursor()
            cur.execute("DELETE FROM chat WHERE id1=%s",(ids,))
            cur.execute("INSERT INTO chat (id1,code,name,req_id) VALUES (%s,%s,%s,%s)",(ids,room,nam,idz))
            mysql.connection.commit()
            cur.close()   
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return 'Room does not exist.'
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        session[6] = room
        return redirect(url_for("room"))
    return render_template("user.html")


@app.route("/room", methods=["POST", "GET"])
def room():
    room = session.get(6)
    cur=mysql.connection.cursor()
    cur.execute('SELECT * FROM chat WHERE code=%s',(room,))
    account = cur.fetchone()
    mysql.connection.commit()
    cur.close()
    disconnect = request.form.get("dis", False)
    if room is None or session.get(2) is None or room not in rooms:
        if disconnect != False:
            disconnect()
        else:
            return redirect(url_for("chathome"))
    return render_template("room.html", code=room, messages=rooms[room]["messages"],data=account)


@app.route("/final", methods=["POST", "GET"])
def final():
    return render_template('final.html')


@socketio.on("message")
def message(data):
    room = session.get(6)
    if room not in rooms:
        return
    content = {
        "name": session.get(2),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get(2)} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
    room = session.get(6)
    name = session.get(2)
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")


@socketio.on("disconnect")
def disconnect():
    room = session.get(6)
    name = session.get(2)
    leave_room(room)
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")


@app.route('/logout',methods=['GET','POST'])
def logout():
    session.clear()
    return render_template('home.html')


@app.route('/confirmed',methods=['GET','POST'])
def confirmed():
    id=session[1]
    cur=mysql.connection.cursor()
    cur.execute('SELECT * FROM request WHERE r_id=%s or s_id=%s and approve>1', (id,id))
    account = cur.fetchall()
    cur.execute('SELECT * FROM user')
    accounts = cur.fetchall()
    return render_template('confirmed.html',requests=account,users=accounts,id=id)


@app.route('/registered',methods=['GET','POST'])
def registered():
    id=session[1]
    cur=mysql.connection.cursor()
    cur.execute('SELECT * FROM booking WHERE s_id=%s', (id,))
    account = cur.fetchall()
    return render_template('registered.html',data=account)
    return render_template('registered.html')

@app.route('/yes',methods=['GET','POST'])
def yes():
    ids=request.form.get("ids")
    cid=str(request.form.get("idz"))
    curs=mysql.connection.cursor()
    curs.execute('SELECT * FROM request WHERE id=%s',(ids,))
    account=curs.fetchone()
    id=account[1] 
    curs.execute("UPDATE request SET approve=approve+1 where id=%s", [[ids]])
    mysql.connection.commit()
    date=str(account[3])
    time=str(account[4])
    passengers1=str(account[6])
    curs.execute('SELECT * FROM booking WHERE s_id=%s AND date=%s AND time=%s', [[id],[date],[time]])
    accounts = curs.fetchone()
    passengers2= accounts[4] - account[6]
    
    if account[7]>1:
        curs = mysql.connection.cursor()
        curs.callproc('InsertRemainingPassenger', [accounts[1], accounts[2], accounts[3], passengers2, accounts[5]])
        mysql.connection.commit()
    
    curs=mysql.connection.cursor()

    #curs.execute("UPDATE booking SET approve=approve+1 where s_id=%s AND date=%s AND time=%s", [[id],[date],[time]])
    #mysql.connection.commit()      
    return redirect(url_for('final'))


@app.route('/edit',methods=['GET','POST'])
def edit():
    keys=request.args.get('id')
    cur=mysql.connection.cursor()
    cur.execute('SELECT * FROM booking WHERE id=%s ', (keys,))
    accounts = cur.fetchone()
    if request.method == 'POST':
        date = request.form['date']
        passengers=request.form['passengers']
        destination=request.form['destination']
        time=request.form['time']
        cur=mysql.connection.cursor()
        cur.execute("UPDATE BOOKING SET date=%s,time=%s,passengers=%s,destination=%s WHERE id=%s",(date,time,passengers,destination,keys))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('registered'))
    return render_template('edit.html',data=accounts) 


@app.route('/no',methods=['GET','POST'])
def no():
    id=request.form.get("ids")
    cid=request.form.get("idz")
    cur=mysql.connection.cursor()
    cur.execute('DELETE FROM request WHERE id=%s', (id,))
    cur.execute('DELETE FROM chat WHERE id=%s',([cid]))
    mysql.connection.commit()
    return redirect(url_for('final'))


if __name__ == "__main__":
    socketio.run(app,debug=True,port=5000)
