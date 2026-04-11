import sys
sys.path.insert(0, 'src')

results = []

# Test 1: Import supervisor
try:
    from heretek_swarm.supervisor import ActorSupervisor
    results.append(("supervisor import", "SUCCESS"))
except Exception as e:
    results.append(("supervisor import", f"FAILED: {e}"))

# Test 2: Instantiate ActorSupervisor
try:
    sup = ActorSupervisor('test', 10.0, True, 3, None)
    results.append(("supervisor instantiation", f"SUCCESS - name={sup.name}, health_check={sup.health_check_interval}"))
except Exception as e:
    results.append(("supervisor instantiation", f"FAILED: {type(e).__name__}: {e}"))

# Test 3: Import factory
try:
    from heretek_swarm.actors.factory import ActorConfig, ActorFactory
    results.append(("factory import", "SUCCESS"))
except Exception as e:
    results.append(("factory import", f"FAILED: {e}"))

# Test 4: Test factory create_actor
try:
    from heretek_swarm.actors.base import AgentActor
    results.append(("base import", "SUCCESS"))
except Exception as e:
    results.append(("base import", f"FAILED: {e}"))

# Print results
for test, result in results:
    print(f"{test}: {result}")