import os, sys, warnings

warnings.filterwarnings('ignore', message=r'Module .*? is being added to sys\.path', append=True)

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))

sys.path = [
    os.path.join(PROJECT_PATH, "../ka-lite-submodule/kalite/packages/dist"),
    os.path.join(PROJECT_PATH, "../ka-lite-submodule/kalite/packages/bundled"),
    os.path.join(PROJECT_PATH, "../"),
    os.path.join(PROJECT_PATH, "../centralserver"),
    os.path.join(PROJECT_PATH, "../", "ka-lite-submodule"),
    os.path.join(PROJECT_PATH, "../", "ka-lite-submodule", "kalite"),
] + sys.path

from django.core.handlers.wsgi import WSGIHandler

os.environ['DJANGO_SETTINGS_MODULE'] = 'centralserver.settings'
application = WSGIHandler()
