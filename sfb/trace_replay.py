"""v3 timing helper only; no Judger, target extraction or answer parser."""

def replay(actions, answers, k=2, q=2):
    if k not in (1, 2, 3) or q not in (1, 2, 3):
        raise ValueError("K/q must be in the frozen nine configurations")
    yes_count, queries = 0, []
    for t, action in enumerate(actions[:100]):
        if type(action) is not int or action not in range(10):
            raise ValueError("Invalid action")
        if action == 0:
            return {"stop_frame": t, "reason": "native", "queries": queries}
        if t % q == 0:
            if t not in answers or type(answers[t]) is not bool:
                raise ValueError(f"Missing verified parsed answer for frame {t}")
            queries.append(t)
            yes_count = yes_count + 1 if answers[t] else 0
            if yes_count >= k:
                return {"stop_frame": t, "reason": "semantic", "queries": queries}
    return {"stop_frame": min(len(actions), 100), "reason": "limit_or_track_end", "queries": queries}
