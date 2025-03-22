from flask import Flask, render_template,request,redirect,url_for # For flask implementation
from pymongo import MongoClient # Database connector
from bson.objectid import ObjectId # For ObjectId to work
from bson.errors import InvalidId # For catching InvalidId exception for ObjectId
import os
import threading # Add threading for timer functionality

mongodb_host = os.environ.get('MONGO_HOST', 'localhost')
mongodb_port = int(os.environ.get('MONGO_PORT', '27017'))
client = MongoClient(mongodb_host, mongodb_port)    #Configure the connection to the database
db = client.camp2016    #Select the database
todos = db.todo #Select the collection

app = Flask(__name__)
title = "TODO with Flask(V2)"
heading = "ToDo Reminder"
#modify=ObjectId()

# Global variables to control health and readiness status
app_healthy = True
app_ready = True
ready_timer = None # Timer to track auto-reset

def redirect_url():
	return request.args.get('next') or \
		request.referrer or \
		url_for('index')

@app.route("/list")
def lists ():
	#Display the all Tasks
	todos_l = todos.find()
	a1="active"
	return render_template('index.html',a1=a1,todos=todos_l,t=title,h=heading)

@app.route("/")
@app.route("/uncompleted")
def tasks ():
	#Display the Uncompleted Tasks
	todos_l = todos.find({"done":"no"})
	a2="active"
	return render_template('index.html',a2=a2,todos=todos_l,t=title,h=heading)


@app.route("/completed")
def completed ():
	#Display the Completed Tasks
	todos_l = todos.find({"done":"yes"})
	a3="active"
	return render_template('index.html',a3=a3,todos=todos_l,t=title,h=heading)

@app.route("/done")
def done ():
	#Done-or-not ICON
	id=request.values.get("_id")
	task=todos.find({"_id":ObjectId(id)})
	if(task[0]["done"]=="yes"):
		todos.update_one({"_id":ObjectId(id)}, {"$set": {"done":"no"}})
	else:
		todos.update_one({"_id":ObjectId(id)}, {"$set": {"done":"yes"}})
	redir=redirect_url()	# Re-directed URL i.e. PREVIOUS URL from where it came into this one

#	if(str(redir)=="http://localhost:5000/search"):
#		redir+="?key="+id+"&refer="+refer

	return redirect(redir)

#@app.route("/add")
#def add():
#	return render_template('add.html',h=heading,t=title)

@app.route("/action", methods=['POST'])
def action ():
	#Adding a Task
	name=request.values.get("name")
	desc=request.values.get("desc")
	date=request.values.get("date")
	pr=request.values.get("pr")
	todos.insert_one({ "name":name, "desc":desc, "date":date, "pr":pr, "done":"no"})
	return redirect("/list")

@app.route("/remove")
def remove ():
	#Deleting a Task with various references
	key=request.values.get("_id")
	todos.delete_one({"_id":ObjectId(key)})
	return redirect("/")

@app.route("/update")
def update ():
	id=request.values.get("_id")
	task=todos.find({"_id":ObjectId(id)})
	return render_template('update.html',tasks=task,h=heading,t=title)

@app.route("/action3", methods=['POST'])
def action3 ():
	#Updating a Task with various references
	name=request.values.get("name")
	desc=request.values.get("desc")
	date=request.values.get("date")
	pr=request.values.get("pr")
	id=request.values.get("_id")
	todos.update_one({"_id":ObjectId(id)}, {'$set':{ "name":name, "desc":desc, "date":date, "pr":pr }})
	return redirect("/")

@app.route("/search", methods=['GET'])
def search():
	#Searching a Task with various references

	key=request.values.get("key")
	refer=request.values.get("refer")
	if(refer=="id"):
		try:
			todos_l = todos.find({refer:ObjectId(key)})
			if not todos_l:
				return render_template('index.html',a2=a2,todos=todos_l,t=title,h=heading,error="No such ObjectId is present")
		except InvalidId as err:
			pass
			return render_template('index.html',a2=a2,todos=todos_l,t=title,h=heading,error="Invalid ObjectId format given")
	else:
		todos_l = todos.find({refer:key})
	return render_template('searchlist.html',todos=todos_l,t=title,h=heading)

@app.route("/about")
def about():
	return render_template('credits.html',t=title,h=heading)

# livenessProbe
@app.route("/health")
def health():
    if app_healthy:
        return {"status": "healthy"}, 200
    else:
        return {"status": "unhealthy"}, 500
# readinessProbe
@app.route("/ready")
def ready():
    if not app_ready:
        return {"status": "not ready", "error": "Readiness manually disabled"}, 503
    try:
        client.server_info() # Check if MongoDB connection is still alive
        return {"status": "ready"}, 200
    except Exception as e:
        return {"status": "not ready", "error": str(e)}, 503

# reset timer for /ready
def reset_ready():
    global app_ready, ready_timer
    app_ready = True
    ready_timer = None
    print("Readiness automatically reset to True after 30 seconds")

# Test endpoints to simulate failures
@app.route("/toggle-health")
def toggle_health():
    global app_healthy
    app_healthy = not app_healthy
    status = "unhealthy" if not app_healthy else "healthy"
    return {"message": f"Health status toggled to {status}"}, 200

# Test endpoint to toggle readiness status
@app.route("/toggle-ready")
def toggle_ready():
    global app_ready, ready_timer
    app_ready = not app_ready
    status = "not ready" if not app_ready else "ready"
    # If toggled to not ready, set timer to reset after 30 seconds
    if not app_ready:
        if ready_timer:
            ready_timer.cancel()
        ready_timer = threading.Timer(30.0, reset_ready)
        ready_timer.daemon = True  # Make thread daemon so it won't block app shutdown
        ready_timer.start()
        return {"message": f"Readiness status toggled to {status}. Will reset in 30 seconds."}, 200
    else:
        if ready_timer:
            ready_timer.cancel()
            ready_timer = None
        return {"message": f"Readiness status toggled to {status}"}, 200

if __name__ == "__main__":
	env = os.environ.get('FLASK_ENV', 'development')
	port = int(os.environ.get('PORT', 5050))
	debug = False if env == 'production' else True
	app.run(host='0.0.0.0', port=port, debug=debug)
	# Careful with the debug mode..