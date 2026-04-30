import argparse
import time

from event_sender import EventSender


def parse_args():
    parser = argparse.ArgumentParser(description="SMART_CLASS camera event worker")
    parser.add_argument("--backend", default="http://127.0.0.1:5000")
    parser.add_argument("--lesson-id", type=int, required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    sender = EventSender(args.backend, args.token)

    # MVP stub: replace this loop with OpenCV detection from EDUCAM123.
    sample_event = {
        "lesson_id": args.lesson_id,
        "event_type": "student_arrived",
        "student_name": "Ученик",
        "payload": {"source": "camera_worker_stub"},
    }

    if args.dry_run:
        print(sample_event)
        return

    sender.send(**sample_event)
    print(f"Sent sample event at {time.strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()

