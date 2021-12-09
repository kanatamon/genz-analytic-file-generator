# The main.py is going to be executing by uWSGI.
# If you're running the application by VS-Code Remote Container, this won't be
# executed.

from app import app
from dotenv import load_dotenv

# NOTE: This is only for development when running container locally on your machine.
# Notice that dotenv won't override the existing ENV. So, it's safe to rest it here,
# even you're running on production.
load_dotenv()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
