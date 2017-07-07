import os

IS_PRODUCTION = not os.environ.get('SERVER_SOFTWARE', '').startswith('Devel')

APPLICATION_ID = ''
AUTHOR_EMAIL = ''
LEGACY_MESSENGER_URL = ''
MESSENGER_DEFAULTS = []

try:
 from configuration import CUSTOM_APPLICATION_ID, \
  CUSTOM_AUTHOR_EMAIL, CUSTOM_LEGACY_MESSENGER_URL, \
  CUSTOM_MESSENGER_DEFAULTS
 AUTHOR_EMAIL = CUSTOM_AUTHOR_EMAIL
 APPLICATION_ID = CUSTOM_APPLICATION_ID
 LEGACY_MESSENGER_URL = CUSTOM_LEGACY_MESSENGER_URL
 MESSENGER_DEFAULTS = CUSTOM_MESSENGER_DEFAULTS
except:
 import logging
 logging.info('No custom configuration defined, or there was an error loading it.')
 AUTHOR_EMAIL = 'user@local.com'
 APPLICATION_ID = 'testapp'

EXTENSION_GALLERY = 'https://chrome.google.com/extensions/detail/'

HOST_NAME = '%s.appspot.com' % APPLICATION_ID
PROTOCOL = 'https'
EMAIL_HOST_NAME = '%s.appspotmail.com' % APPLICATION_ID
BUG_DATABASE_NO_REPLY_EMAIL = 'bug-database-no-reply@%s' % EMAIL_HOST_NAME
NO_REPLY_EMAIL = 'no-reply@%s' % EMAIL_HOST_NAME

if not IS_PRODUCTION:
 HOST_NAME = 'localhost:8080'
 PROTOCOL = 'http'
ORIGIN = '%s://%s' % (PROTOCOL, HOST_NAME)
PATH = os.path.join(os.path.dirname(__file__), 'content-template.html')