import os

from django.conf import settings
from django.test import TestCase
from tribunales.models import Asignatura, Headquarter, Sede

from .views import get_moves


class HeadquartersMoveTestCase1(TestCase):
    def setUp(self):
        self.asignatura = Asignatura.objects.create(COD_ASIGNATURA=1)

        sede1 = Sede.objects.create(COD_SEDE=1)
        sede2 = Sede.objects.create(COD_SEDE=2)
        sede3 = Sede.objects.create(COD_SEDE=3)
        sede4 = Sede.objects.create(COD_SEDE=4)

        Headquarter.objects.create(COD_SEDE=sede1, COD_ASIGNATURA=self.asignatura, EVALUADORES=1, EXAMENES=10)
        Headquarter.objects.create(COD_SEDE=sede2, COD_ASIGNATURA=self.asignatura, EVALUADORES=1, EXAMENES=3)
        Headquarter.objects.create(COD_SEDE=sede3, COD_ASIGNATURA=self.asignatura, EVALUADORES=0, EXAMENES=2)
        Headquarter.objects.create(COD_SEDE=sede4, COD_ASIGNATURA=self.asignatura, EVALUADORES=1, EXAMENES=15)

    def test_get_moves(self):
        # Call get_moves function
        moves_data = get_moves(self.asignatura)

        # Expected results (you need to define these based on your logic)
        expected_mean = 10  # Sample expected mean
        expected_total_moves = 3  # Sample expected total moves
        print(moves_data["move_details"])
        # expected_move_details = [
        #         {'from_HQ': 3, 'to_HQ': 2, 'num_moves': 2},
        #         {'from_HQ': 4, 'to_HQ': 2, 'num_moves': 5}
        #         ]

        # Compare actual results with expected results
        self.assertEqual(moves_data["mean"], expected_mean)
        self.assertEqual(moves_data["total_moves"], expected_total_moves)
        # self.assertEqual(moves_data['move_details'], expected_move_details)


#    def test_render_moves(self):
#        response = get_moves(self.client.get('/'))
#        self.assertEqual(response.status_code, 200)
#        self.assertEqual(response.context['mean'], 25)  # Adjust mean according to your test data
#        self.assertEqual(response.context['total_moves'], 0)  # Adjust total_moves according to your test data
#        # Add more assertions as needed for move_details


class HeadquartersMoveTestCase2(TestCase):
    def setUp(self):
        test_files_dir = os.path.join(settings.BASE_DIR, "tribunales_evau/tribunales/testfiles")

        # Create Sede objects if they don't exist yet
        sedes = {}
        files = []
        for filename in os.listdir(test_files_dir):
            if filename.endswith(".dzn"):
                filepath = os.path.join(test_files_dir, filename)
                files.append(filename)
                with open(filepath) as file:
                    lines = file.readlines()
                    n = int(lines[0].split("=")[1].strip("; \n"))
                    for i in range(n):
                        if i not in sedes:
                            sedes[i] = Sede.objects.create(COD_SEDE=i + 1)

        self.asignaturas = []
        for filename in files:
            filepath = os.path.join(test_files_dir, filename)
            with open(filepath) as file:
                # Read data from the text file
                lines = file.readlines()
                headquarter_data = [tuple(map(int, line.strip("| ").split(","))) for line in lines[2:-2]]
                headquarter_data.insert(0, lines[1][-7:-1].strip("| ").split(","))

                # Create Sede and Asignatura objects
                asignatura_name = filename.split("_")[1].split(".")[0]  # Extract asignatura name from filename
                asignatura = Asignatura.objects.create(ASIGNATURA=asignatura_name)
                self.asignaturas.append(asignatura)

                # Create Headquarter objects
                for i, data in enumerate(headquarter_data):
                    exams, evaluadores = data
                    Headquarter.objects.create(
                        COD_SEDE=sedes[i], COD_ASIGNATURA=asignatura, EVALUADORES=evaluadores, EXAMENES=exams
                    )

    def test_get_moves(self):
        # Expected results
        # expected_mean = 10  # Sample expected mean
        # expected_total_moves = 3  # Sample expected total moves

        # Call get_moves function
        for asignatura in self.asignaturas:
            print("")
            print("Asignatura: " + asignatura.ASIGNATURA)
            moves_data = get_moves(asignatura)

            print("Mean: " + str(moves_data["mean"]))
            print("Moves: " + str(moves_data["total_moves"]))
            print(moves_data["move_details"])

            # Assert results
            # self.assertEqual(moves_data['mean'], expected_mean)
            # self.assertEqual(moves_data['total_moves'], expected_total_moves)
            # self.assertEqual(moves_data['move_details'], expected_move_details)
