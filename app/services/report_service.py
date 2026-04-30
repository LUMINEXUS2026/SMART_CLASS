from collections import Counter


def count_events(events):
    return Counter(event.event_type for event in events)

