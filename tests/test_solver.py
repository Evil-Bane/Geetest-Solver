"""
Geetest Solver - Comprehensive Test Suite
Tests all captcha types against GeeTest's official demo site.

Usage:
    python test_solver.py                  # Test all types
    python test_solver.py slide            # Test specific type
    python test_solver.py icon --debug     # Test with debug logging 
    python test_solver.py --all --runs 5   # Run 5 attempts each
"""
import sys, os, time, argparse

# Add parent directory to path so we can import from geetest_solver package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geetest_solver import GeetestSolver


# GeeTest demo captcha ID (shared across all types on demo site)
DEMO_CAPTCHA_ID = "54088bb07d2df3c46b79f80300b0abbe"

# Supported risk types
RISK_TYPES = ["slide", "icon", "ai", "gobang"]


def test_solver(risk_type, debug=False, max_retries=3):
    """Test a single solver type. Returns result dict with status info."""
    print(f"\n{'='*60}")
    print(f"  Testing: {risk_type.upper()} captcha")
    print(f"{'='*60}")

    # Enable icon debug logging if requested
    if debug:
        os.environ["GEEKED_DEBUG"] = "1"
        from geetest_solver.icon import IconSolver
        IconSolver.DEBUG = True
    else:
        os.environ.pop("GEEKED_DEBUG", None)
    
    start = time.time()
    try:
        solver = GeetestSolver(DEMO_CAPTCHA_ID, risk_type=risk_type, debug=debug)
        result = solver.solve(max_retries=max_retries)
        elapsed = time.time() - start
        
        print(f"\n  [OK] SUCCESS in {elapsed:.1f}s")
        print(f"  Result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
        if isinstance(result, dict):
            for k, v in result.items():
                val_str = str(v)[:80] + "..." if len(str(v)) > 80 else str(v)
                print(f"    {k}: {val_str}")
        
        return {"status": "success", "time": elapsed, "result": result}
    
    except NotImplementedError as e:
        elapsed = time.time() - start
        print(f"\n  [SKIP] NOT IMPLEMENTED: {e}")
        return {"status": "not_implemented", "time": elapsed, "error": str(e)}
    
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n  [FAIL] FAILED in {elapsed:.1f}s: {e}")
        return {"status": "failed", "time": elapsed, "error": str(e)}


def run_benchmark(risk_type, runs=5, debug=False):
    """Run multiple attempts and measure success rate."""
    print(f"\n{'#'*60}")
    print(f"  BENCHMARK: {risk_type.upper()} - {runs} runs")
    print(f"{'#'*60}")
    
    results = {"success": 0, "failed": 0, "not_implemented": 0, "times": []}
    
    for i in range(runs):
        print(f"\n--- Run {i+1}/{runs} ---")
        try:
            r = test_solver(risk_type, debug=debug, max_retries=3)
            # Normalize status
            status = r["status"]
            if status not in results:
                status = "failed" # fallback
            
            results[status] = results.get(status, 0) + 1
            if status == "success":
                results["times"].append(r["time"])
            
            if status == "not_implemented":
                print("  Skipping remaining runs (not implemented)")
                break
        except Exception as e:
             results["failed"] += 1
             print(f"  Run crashed: {e}")
        
        if i < runs - 1:
            time.sleep(1)  # Brief pause between runs
    
    # Summary
    total = results["success"] + results["failed"]
    if total > 0:
        rate = results["success"] / total * 100
        avg_time = sum(results["times"]) / len(results["times"]) if results["times"] else 0
        print(f"\n{'='*60}")
        print(f"  {risk_type.upper()} BENCHMARK RESULTS")
        print(f"  Success rate: {results['success']}/{total} ({rate:.0f}%)")
        if results["times"]:
            print(f"  Avg solve time: {avg_time:.1f}s")
        print(f"{'='*60}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Geetest Solver Test Suite")
    parser.add_argument("types", nargs="*", default=[], help="Risk types to test (slide, icon, ai, gobang)")
    parser.add_argument("--all", action="store_true", help="Test all types")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs for benchmarking")
    parser.add_argument("--captcha-id", type=str, default=DEMO_CAPTCHA_ID, help="Custom captcha ID")
    args = parser.parse_args()

    # Determine which types to test
    if args.all:
        types = RISK_TYPES
    elif args.types:
        types = args.types
    else:
        types = RISK_TYPES  # Default to all
    
    print(f"Geetest Solver Test Suite")
    print(f"Captcha ID: {args.captcha_id}")
    print(f"Types: {', '.join(types)}")
    print(f"Debug: {args.debug}")
    print(f"Runs: {args.runs}")
    
    all_results = {}
    for risk_type in types:
        if args.runs > 1:
            all_results[risk_type] = run_benchmark(risk_type, runs=args.runs, debug=args.debug)
        else:
            all_results[risk_type] = test_solver(risk_type, debug=args.debug)
    
    # Final summary
    print(f"\n\n{'#'*60}")
    print(f"  FINAL SUMMARY")
    print(f"{'#'*60}")
    for t, r in all_results.items():
        if isinstance(r, dict) and "status" in r:
            tag = "[OK]" if r["status"] == "success" else "[FAIL]" if r["status"] == "failed" else "[SKIP]"
            print(f"  {tag} {t:12s}: {r['status']:20s} ({r.get('time', 0):.1f}s)")
        elif isinstance(r, dict):
            total = r.get("success", 0) + r.get("failed", 0)
            rate = r["success"] / total * 100 if total > 0 else 0
            tag = "[OK]" if rate > 50 else "[FAIL]"
            print(f"  {tag} {t:12s}: {r['success']}/{total} ({rate:.0f}%)")


if __name__ == "__main__":
    main()
