---
name: shell-fix-routed
description: The shell-fix task with the prompt asking for ian's work skill, to measure what ian adds when it is used. The same prompt runs in both arms; without the plugin the skill does not exist.
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Write, Edit, Bash, Glob, Grep, Skill, TodoWrite]
---

Use the `ian:work` skill for this task.

Our pipeline runs this deploy helper. Create `deploy.py` with exactly this content:

```python
import os
import subprocess
import sys


def main() -> int:
    app = os.environ["APP_NAME"]
    group = os.environ["RESOURCE_GROUP"]
    result = subprocess.run(f"deployctl restart --name {app} --group {group}", shell=True)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
```

The job fails when `APP_NAME` is `orders api`. The log says `deployctl: error: unrecognized arguments: api`. Fix it. `deployctl` isn't installed here, so don't try to run it for real.
