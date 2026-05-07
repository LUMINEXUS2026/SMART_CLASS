# Smart Class MVP activity metrics

Owner: Головин Егор and Соколов Лёша.

The MVP activity score is intentionally simple. It is not a psychological score and must not be used as a punishment trigger.

## Input signals

- Time in lesson module.
- Active actions: page open, page change, task start, task complete, answer check, help request.
- Inactive actions: hidden tab, pause, long idle, stalled task.
- Long pauses and repeated stalled states.

## Formula

Base score: `55`.

Add:

- `+6` for each active action.
- `+1` for each active minute, capped at `+20`.

Subtract:

- `-8` for each inactive action.
- `-1` for each 30 seconds of idle time, capped at `-22`.

Final score is clamped between `0` and `100`.

## Status examples

- `85-100`: steady active work.
- `65-84`: normal activity.
- `45-64`: low activity, watch gently.
- `<45`: teacher should check context.

## Important rule

If the teacher blocks a student in the camera view, the system does not mark the student absent or left. Camera absence only becomes a warning after the student was last seen near an exit zone and then disappeared for the configured threshold.
