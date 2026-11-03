# Fix

A script or job is broken. Every changed line traces to evidence.

1. Get the exact failure: the log lines, the exit code, the inputs, and the commit that ran. A description of a failure is not the failure, so find the log.
2. Reproduce it locally. List the environment variables and arguments the entry point reads, set them to the failing values, and run it. Or write a test that drives the entry point the same way. If you can't reproduce it, say what blocks you, and get as close as you can.
3. Find the first wrong value. Walk the data path (input, parsed value, decision, command or API call) and check each hop with a print, a debugger, or a test. Drop each hypothesis the evidence refutes, along with any code it motivated.
4. Write a failing test at the boundary that shows the bug: the exit code, the argv, the output, or a file. Run it and keep the failing output.
5. Make the smallest fix at the first wrong value. Check it against principles 3, 5, 7, and 8.
6. Run the test, which now passes, then the verify skill. If anything outside this repo consumes the code, run impact.
7. Order the commits so the failing test comes before the fix. Get the fix to P4 with a real pipeline run, or say why you couldn't.

**Report:** the failure, the root cause with its evidence, the fix, and the failing-then-passing output.
