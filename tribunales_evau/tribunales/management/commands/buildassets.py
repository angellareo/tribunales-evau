import os
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Build static assets"
    name = "buildstatic"

    def handle(self, *args, **options):
        # Step 1: Remove a directory
        os.system("rm -rf tribunales_evau/static/vue")
        os.system("rm -rf " + settings.STATIC_ROOT + "/*")

        # Step 2: Change directory and run npm run build
        os.chdir("vue-frontend")
        subprocess.run(["npm", "run", "build"])

        # Step 3: Change back to previous directory and run collectstatic
        os.chdir(settings.BASE_DIR)
        subprocess.run(["python", "manage.py", "collectstatic"])
