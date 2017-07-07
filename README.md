# test-app
My very first Python application, Google App Engine based, from 2008 onward, which includes a guestbook, an issue tracker, a partial XMPP assisted messenger and flair images.

## Notes
- Some of the features are obsolete, or rely on obsolete applications.
- Do not take this as an example for good code. It was just something I hacked up quickly over the years for various unimportant needs.
- The issue tracker is not trying to be secure in any way. You can use HTML freely and it will indeed run scripts. Do not even bother and do not rely on this.
- It is open source for historical and ideological reasons.

## Running from Google Cloud Shell
```shell
./serve.sh
```

## Running without Google Cloud Shell
```shell
dev_appserver.py .
```
## Customization options
Add a file named `configuration.py` that defines any, a few or all of the variables from the following example -
```
CUSTOM_LEGACY_MESSENGER_URL = 'http://www.legacymessenger.com'
CUSTOM_APPLICATION_ID = 'test-cool-app'
CUSTOM_AUTHOR_EMAIL = 'tester@test.com'
CUSTOM_MESSENGER_DEFAULTS = \
 [ \
  [CUSTOM_AUTHOR_EMAIL, 'Me', 'You'], \
  ['some@gmail.com', 'You', 'Me'], \
  ['grip@gmail.com', 'Grip', 'Me'] \
 ]
CUSTOM_GITHUB_REPOSITORY = 'https://github.com/tester/test-app/'
CUSTOM_APPLICATION_TITLE = 'Applifier'
CUSTOM_COPYRIGHT_YEAR_RANGE = '2022'
CUSTOM_COPYRIGHT_HOLDER = 'Bug'
```

## License
MIT. Do whatever you want, basically.