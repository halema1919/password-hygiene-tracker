#Imports
from flask import Flask, render_template, redirect, request, jsonify
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


# My App
app=Flask(__name__)
Scss(app)

#configure 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
#new db for each user
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db=SQLAlchemy(app)


#data class, row of data, one row of data, for each row
class Account(db.Model):
    #each item will have unique id
    id = db.Column(db.Integer, primary_key=True) #helps add and delete things
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated= db.Column(db.DateTime, default=datetime.utcnow)
    last_reviewed= db.Column(db.DateTime, default=datetime.utcnow)

    #not returning anything ^ so have to: 
    def __repr__(self) -> str: 
        return f"Account{self.id}"

    @property
    def status(self):
        days = (datetime.utcnow() - self.last_reviewed).days
        if days >= 90:
            return "review-recommended"
        elif days >= 60:
            return "review-soon"
        else:
           return "ok"
    
with app.app_context():
    db.create_all()


#Home page
#routes to webpages

@app.route("/dismiss/<int:id>", methods=["POST"])
def dismiss(id:int):
    #look up account by id
    account = Account.query.get_or_404(id)
    #reset last_reviewed to now
    account.last_reviewed = datetime.utcnow()

    try:
        db.session.commit()
        return redirect("/")
    except Exception as e:
        return f"Error:{e}"



@app.route("/mark-updated/<int:id>", methods=["POST"])
def mark_updated(id: int):
    # look up account 
    account = Account.query.get_or_404(id)

    # capture one timestamp, which will be used for both fields
    # timestamp comes from the server

    now = datetime.utcnow()

    #record that the password itself was actually changed
    account.last_updated = now
    # confirming an update also counts as reviewing it, so we wanna reset this too
    account.last_reviewed = now

    try:
        db.session.commit()
        return redirect("/")
    except Exception as e:
        return f"Error:{e}"

# this route is for the checker page
@app.route("/checker/<int:id>")
def checker(id: int):
    # look up which account this check is for
    account = Account.query.get_or_404(id)
    #render the checker page 
    return render_template('checker.html', account=account)

#route for marking an account as reviewd
@app.route("/mark-reviewed/<int:id>", methods=["POST"])
def mark_reviewed(id: int):
    # look up the account being marked as reviewed
    account = Account.query.get_or_404(id)
    #reset the review clock  
    account.last_reviewed = datetime.utcnow()

    try:
        db.session.commit()
        # responds with json
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/", methods=["POST","GET"])
def index(): 
    #add a new account
    if request.method == "POST":
        # read the account name and category from the form
        current_name=request.form['name']
        current_category=request.form['category']

        #ceate an Account object with the given name and category
        new_account= Account(name=current_name, category=current_category)

    
        #send to db
        try: 
            db.session.add(new_account)
            db.session.commit()
            return redirect ("/")
        except Exception as e:
            print(f"Error:{e}")
            return f"Error:{e}"
     #see all 
    else:
        #get the accounts from db, order by last updated, ascending:
        accounts = Account.query.order_by(Account.last_updated.asc()).all()
        #render the index.html template and pass the accounts to it
        return render_template('index.html', accounts=accounts)
    


#Delete an Item
@app.route("/delete/<int:id>")
def delete(id:int):
    delete_account=Account.query.get_or_404(id)
    try: 
        db.session.delete(delete_account)
        db.session.commit()
        return redirect ("/")
    except Exception as e:
        return f"Error:{e}"

#edit an Item
@app.route("/edit/<int:id>", methods=["GET", "POST"])
#edit by an id
def edit(id:int):
    account=Account.query.get_or_404(id)
    if request.method == "POST":
        account.name=request.form['name'] #update
        try:
            db.session.commit()
            return redirect("/")
        except Exception as e:
            return f"Error:{e}"
    else: 
        return render_template('edit.html', account=account)




#Runner and debugger
if __name__ == "__main__":
   


    app.run(debug=True, port=5000)