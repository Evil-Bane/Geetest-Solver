from geetest_solver import GeetestSolver

# Test configuration
CAPTCHA_ID = "54088bb07d2df3c46b79f80300b0abbe"
RISK_TYPE = "slide" 

print(f"Initializing solver for {RISK_TYPE}...")
solver = GeetestSolver(CAPTCHA_ID, RISK_TYPE)
result = solver.solve()
print("Result:", result)
