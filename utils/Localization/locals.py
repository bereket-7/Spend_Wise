import gettext
import os

# Set up localization
LOCALE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'localization')
LANGUAGES = ['en', 'am'] 

def setup_localization():
    translation = gettext.translation(domain='messages', localedir=LOCALE_DIR, languages=LANGUAGES, fallback=True)
    translation.install()

setup_localization()

def greet_user():
    print(_("Hello, welcome to SpendWise  application!"))

def announce_count(count):
    print(_("There are %(count)s items.") % {'count': count})

if __name__ == "__main__":
    greet_user()
    announce_count(5)
