import os

# LDAP authentication example configuration, requires django-auth-ldap package
# try:
#     import ldap
#     from django_auth_ldap.config import LDAPSearch
#     AUTHENTICATION_BACKENDS = ["django_auth_ldap.backend.LDAPBackend"]
#     AUTH_LDAP_SERVER_URI = "ldap://__ldap_server__/"

#     AUTH_LDAP_BIND_DN = ""
#     AUTH_LDAP_BIND_PASSWORD = ""
#     AUTH_LDAP_USER_SEARCH = LDAPSearch(
#         " cn=__some__,dc=__ldap__,dc=__de__", ldap.SCOPE_SUBTREE, "(uid=%(user)s)"
#     )
# except:
#     pass


# Mailing
### backend for testing, comment for production
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Python has a little SMTP server built-in. You can start it in a second console with this command:
# python -m smtpd -n -c DebuggingServer localhost:1025
# This will simply print all the mails sent to localhost:1025 in the console.
# You have to configure Django to use this server in your settings.py:
# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 1025

### production email configuration
# EMAIL_HOST = '__mailserver__'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = '__mailuser__'
# EMAIL_HOST_PASSWORD = '__mailuserpw__'
# EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = '__from-email__'

DEBUG = True
PRIVACY_NOTICE = True