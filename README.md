A small application for allowing people to register to an event. Originally developed for the famous X-mas lecture at the ALU-Freiburg.

Admins can create events that are open for registration for a specified period.
Events have a limit on the number of registrants (or 'seats') per user and on the total number of registrants (or 'seats').
Admins can download a pdf with the registrated people for an event.

Users can register for the event. After filling the registration form, they receive 
an email with a link to confirm their registration. This is required to make sure the
user didn't enter a bogus email and to prevent bogus registrations.

After users confirme the registration, they receive another email in order to confirm their confirmation.

# Setup
The following commands have to be executed to initialize the project
```
# generate sql statements
python manage.py makemigrations registration
# if you have added/modified l10n
python manage.py makemessages -l de -l en 
python manage.py compilemessages
# create sql tables
python manage.py migrate
```

In case you want a superuser, execute
`python manage.py createsuperuser`.


# Deployment
Adjust the `mysite/local_settings.py`. At least, you've to 
* adjust the value for `SECRET_KEY`
* set `DEBUG=True` or set appropriate `ALLOWED_HOSTS`

These values can also be set via environment variables.  
If you've a banner, put it in `registration/static/registration/banner.jpg`.

Then, run
```
python manage.py runserver
``` 
and the will be accessible at `localhost:8000/registration`.

For a proper deployment, use nginx with wsgi or s.t. like that. 
You then need take care of your statics on your one, collect them with  
```
python manage.py collectstatic
```
One may use [gotzl/docker-django-uwsgi-nginx](https://github.com/gotzl/docker-django-uwsgi-nginx) as a starting point.
