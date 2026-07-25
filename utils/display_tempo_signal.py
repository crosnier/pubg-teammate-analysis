# ==============================
# utils/display_tempo_signal.py
# ==============================


def render_tempo_signal(signal):
    print("=============================")
    print("⏱️  Archetype Tag - Tempo")
    print("=============================")

    tempo_tag = signal["tempo_tag"]
    matches_analyzed = signal["matches_analyzed"]
    matches_with_contact = signal["matches_with_contact"]

    if tempo_tag is None:
        print("No cached telemetry with a real-player engagement yet.")
        return

    print(f"Tempo tag: {tempo_tag}")
    plural = "es" if matches_analyzed != 1 else ""
    print(f"(from {matches_with_contact}/{matches_analyzed} cached match{plural} with an early engagement)")
    print()

    width = max(len(bucket) for bucket in signal["bucket_counts"])
    for bucket, count in sorted(signal["bucket_counts"].items(), key=lambda kv: kv[1], reverse=True):
        print(f"{bucket:<{width}} : {count}")
