---
type: regex
target: trace
pattern: "=== THE REPORT AS WRITTEN ===[\\s\\S]*CHK-418[\\s\\S]*=== END OF THE REPORT ==="
weight: 1
---
The report file shows the failed check's finding.

The script copies the check's report into the file, but the eval's sandbox hides the plugin's data
folder, where the hook keeps it, from commands, so here the finding reaches the file through
Claude's own account of why the build stopped; the copy is checked by the unit tests and the
install trial.
