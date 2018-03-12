"""
    Data imported by GAMSApp to configure program behaviour
"""

# Used by GamsModel.check_model_status
model_status_map  = { 4  : 'Infeasible model found.',
                      5  : 'Locally infeasible model found.',
                      6  : 'Solver terminated early and model was still infeasible.',
                      7  : 'Solver terminated early and model was feasible but not yet optimal.',
                      11 : 'GAMS and/or solver licensing problem.',
                      12 : 'Error: Unknown cause.',
                      13 : 'Error: No solution attained.',
                      14 : 'No solution returned.',
                      18 : 'Unbounded: No solution.',
                      19 : 'Infeasible: No solution.'
                    }

default_model_status_msg = "Unknown model status"

# Used by GamsModel.check_solver_status
solver_status_map = { 2  : "Solver ran out of iterations",
                      3  : "Solver exceeded time limit",
                      4  : "Solver quit with a problem",
                      5  : "Solver quit with nonlinear term evaluation errors",
                      6  : "Solver terminated because the model is beyond the solvers capabilities",
                      7  : "Solver terminated with a license error",
                      8  : "Solver terminated on users request (e.g. Ctrl+C)",
                      9  : "Solver terminated on setup error",
                      10 : "Solver terminated with error",  # duplicate
                      11 : "Solver terminated with error",  # duplicate
                      12 : "Solve skipped",
                      13 : "Other error",
                      14 : "Undefined condition"
                    }

default_solver_status_msg = "Unknown solver status"
