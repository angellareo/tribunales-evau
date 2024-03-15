from django.shortcuts import render
from pulp import LpMinimize, LpProblem, LpVariable, lpSum, value
from pulp.apis import PULP_CBC_CMD
from tribunales.models import Headquarter


def get_moves(asignatura):
    # Retrieve data from Headquarter model
    # headquarters = Headquarter.objects.all()
    headquarters = Headquarter.objects.filter(COD_ASIGNATURA=asignatura)

    # Organize data into a dictionary for easier processing
    headquarter_data = {}
    for headquarter in headquarters:
        sede_id = headquarter.COD_SEDE_id
        if sede_id not in headquarter_data:
            headquarter_data[sede_id] = {"exams": 0, "evals": 0}
        headquarter_data[sede_id]["exams"] += headquarter.EXAMENES
        headquarter_data[sede_id]["evals"] += headquarter.EVALUADORES

    # Calculate mean
    mean = sum(data["exams"] for data in headquarter_data.values()) // sum(
        data["evals"] for data in headquarter_data.values()
    )

    # Create a LP problem
    prob = LpProblem("Headquarters_Movement", LpMinimize)

    # Decision variables
    HQ = list(headquarter_data.keys())
    # print("HQ: "+str(HQ))

    # num_moves = LpVariable("num_moves", lowBound=0, cat="Integer")  # The number of moves
    num_exchanges = LpVariable("num_exchanges", lowBound=0, cat="Integer")  # The number of exchanges

    moves = LpVariable.dicts("moves", (HQ, HQ), lowBound=0, cat="Integer")
    exchanges = LpVariable.dicts("exchange", ((i, j) for i in HQ for j in HQ), cat="Binary")

    # Constraints
    for i in HQ:
        for j in HQ:
            prob += moves[i][j] >= 0
            prob += (
                moves[i][j] <= headquarter_data[i]["exams"] * exchanges[i, j]
            )  # No movements allowed if exchange[i][j] = 0
            prob += moves[i][j] <= max(
                0,
                min(
                    (headquarter_data[i]["exams"] - (mean * headquarter_data[i]["evals"])),
                    max((mean * headquarter_data[j]["evals"]) - headquarter_data[j]["exams"], 0),
                ),
            )

    for i in HQ:
        prob += lpSum(moves[i][j] for j in HQ) <= max(
            headquarter_data[i]["exams"] - (mean * headquarter_data[i]["evals"]), 0
        )

    for j in HQ:
        prob += lpSum(moves[i][j] for i in HQ) >= (mean * headquarter_data[j]["evals"]) - headquarter_data[j]["exams"]

    # Total number of exams moved - not needed
    # prob += num_moves == lpSum(moves[i][j] for i in HQ for j in HQ)

    # Define total number of exchanges
    prob += num_exchanges == lpSum([exchanges[i, j] for i in HQ for j in HQ])

    # Objective: minimize the number of exchanges
    prob += num_exchanges

    prob.solve(PULP_CBC_CMD(msg=False))

    # Output the results
    total_moves = value(prob.objective)
    move_details = []
    for i in HQ:
        for j in HQ:
            if value(moves[i][j]) > 0:
                move_details.append({"from_HQ": i, "to_HQ": j, "num_moves": int(value(moves[i][j]))})
    return {"mean": mean, "total_moves": total_moves, "move_details": move_details}


def render_moves(request):
    return render(request, "moves_template.html", get_moves(request))
