from typing import Dict, List

MAX_WORDS = 250


def count_words(text: str) -> int:
    return len(text.split()) if isinstance(text, str) else 0


def assemble_final_pulse(theme_summaries: List[Dict], title: str = "Weekly Pulse Summary") -> Dict:
    sections = [title]
    for theme in theme_summaries:
        sections.append(f"{theme['theme']}: {theme['summary']}")

    full_text = "\n\n".join(sections)
    word_count = count_words(full_text)

    if word_count <= MAX_WORDS:
        return {
            "pulse_text": full_text,
            "word_count": word_count,
            "themes": theme_summaries,
        }

    # Truncate intelligently by reducing summaries.
    truncated_sections = [title]
    for theme in theme_summaries:
        truncated_text = " ".join(theme["summary"].split()[:max(8, min(20, len(theme["summary"].split())) )])
        truncated_sections.append(f"{theme['theme']}: {truncated_text}...")

    full_text = "\n\n".join(truncated_sections)
    tokens = count_words(full_text)
    if tokens > MAX_WORDS:
        full_text = " ".join(full_text.split()[:MAX_WORDS])
        tokens = MAX_WORDS

    return {
        "pulse_text": full_text,
        "word_count": tokens,
        "themes": theme_summaries,
    }


def build_output_payload(
    phase: int,
    review_count: int,
    sampled_count: int,
    theme_analysis: List[Dict],
    summary: Dict,
) -> Dict:
    return {
        "phase": phase,
        "timestamp": summary.get("timestamp"),
        "review_count": review_count,
        "sampled_count": sampled_count,
        "theme_analysis": theme_analysis,
        "summary": summary,
    }
