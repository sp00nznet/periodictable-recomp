# Roadmap

## Next
- Make the harness steady: reruns differ in the caption and menu bar
  (window activation), a different step each run. Capture the client area,
  or activate both windows the same way, and get back to 3 of 3 every run.
- Check the rest of the program against the original: File > Print Element
  Info and Print Chart (print to a file printer and compare), Help > About,
  the Key form, Help > Check for Update (msinet; offline it says "You are not
  connected to the Internet").
- More harness steps: every element by click and by search, a search that
  finds nothing ("Sorry, Could not find element!"), so the figure is a count
  over a corpus.
- Track the harness figure over time and fail on regression (REPO_RULES
  section 9): a `conformance.json` baseline.

## Then
- Headless mode, `--headless --record out.mp4` (REPO_RULES section 10). Today
  the harness runs on a hidden desktop (`tools/rp.py`), which already works
  over RDP, but there is no recording.
- The 10 functions whose extent walk found no terminator: check none is reached.

## Out of scope
- The trial. The program keeps its own 5-day trial in the registry, and the
  recompilation runs it unchanged: no registration is bypassed.
- Rewriting or changing what the program shows. The point is the original's
  window, pixel for pixel.
