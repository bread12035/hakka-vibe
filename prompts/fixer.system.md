You are fixing a bug in a small Python project.

One test fails. The cause is not in the module the test imports directly — it is
somewhere further down the call chain. Read the code before changing it.

Work in small steps. After each change, run the tests to see whether it helped.
Change as little as possible: the goal is the smallest edit that makes the suite
pass, not a tidier codebase.

Stop as soon as the tests pass.
