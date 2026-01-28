from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from date_parsing import *


app = Flask(__name__, static_folder="static", template_folder="templates")


# /// = relative path, //// = absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    date_time = db.Column(db.DateTime)
    is_all_day = db.Column(db.Boolean, default=False)  


@app.route("/")
def home():
    event_list = Event.query.all()
    return render_template("home.html", event_list=event_list)


@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    cleaned_title = clean_title_date(title)

    # Handle "[nth] of [month] [year]" format
    parsed_date, is_invalid_date = parse_nth_of_month(cleaned_title)

    # Handle "nth weekday of next month" format (now with improved invalid detection)
    if parsed_date is None and "next month" in cleaned_title:
        parsed_date, is_invalid_date = parse_nth_weekday_of_next_month(cleaned_title)

    # Validate structured dates before general parsing to catch cases like "31/04"
    # If invalid, skip parsing and set to None
    elif parsed_date is None and not is_invalid_date:
        if not validate_structured_date(cleaned_title):
            parsed_date = None  # Explicitly invalid structured date
        else:
            try:
                # Make parsing stricter: Try without fuzzy first for better error handling
                parsed_date = parse_simple_date(cleaned_title)
                # Parse with dateparser's search_dates() to correct potential mistakes made by dateutil
                if ("tomorrow" in cleaned_title or 
                    is_same_weekday_as_today(cleaned_title) or
                    parsed_date is None or 
                    parsed_date < datetime.now()
                ):
                    parsed_date = parse_relative_natural_language_dates(cleaned_title)
            except (ValueError, OverflowError):
                # Now explicitly sets to None on parsing errors for invalid dates
                parsed_date = None

    # If parsed_date is None (e.g., due to invalid date), ensure we don't proceed with bad data
    # Clean the title only if we have a valid parsed_date (as per original logic)
    cleaned_event_title = title
    if parsed_date:
        cleaned_event_title = remove_date_from_title(title)
        
    # Determine if this is an all-day event based on whether a time was specified
    is_all_day = not time_is_specified(cleaned_title)
    
    # Create the new event with the all-day flag
    new_event = Event(
        title=cleaned_event_title, 
        date_time=parsed_date,
        is_all_day=is_all_day
    )
    db.session.add(new_event)
    db.session.commit()
    
    return redirect(url_for("home"))


@app.route("/edit", methods=["POST"])
def edit():
    event_id = request.form.get("event_id")
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        return redirect(url_for("home"))
    
    title = request.form.get("title")
    date = request.form.get("date")
    time = request.form.get("time")

    event.title = title
    event.is_all_day = not time
    if date and time:
        try:
            # Combine date and time into a single datetime object
            event.date_time = parse(f"{date} {time}")
        except ValueError:
            # If parsing fails, set date_time to None
            event.date_time = None
    else:
        event.date_time = None
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete/<int:event_id>")
def delete(event_id):
    event = Event.query.filter_by(id=event_id).first()
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for("home"))


@app.cli.command("init_db")
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Initialized the database.")

if __name__ == "__main__":
    app.run(debug=True)
    