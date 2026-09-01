# Harness token cost experiments — summary report

No run data exists yet. Every experiment is still in-progress pending real API calls against the synthetic fixture.

## Known limitations

- The fixture is synthetic. Relative differences between arms are
  trustworthy; absolute dollar figures do not transfer to real projects.
- The fixture-generating model and the model under measurement are in the
  same family, a validity threat the mechanically-injected bug reduces but
  does not remove.
- Self-built-harness results (5 minute cache TTL) and Claude Code results
  (fixed 1 hour TTL) are priced on different bases and are not comparable to
  each other, even for the same nominal experiment.
