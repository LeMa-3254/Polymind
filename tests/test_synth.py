from datetime import date
import unittest

from pipeline.synth import current_week_bounds, fallback_synthesis, synthesize_week


class FakeModelClient:
    def complete_json(self, **kwargs):
        return {"synthesis_md": "## Model Synthesis\n\nA short weekly narrative."}, {"input_tokens": 4}


class SynthTests(unittest.TestCase):
    def test_current_week_bounds_uses_monday_to_sunday(self):
        self.assertEqual(current_week_bounds(date(2026, 6, 29)), ("2026-06-29", "2026-07-05"))

    def test_fallback_synthesis_groups_by_theme(self):
        markdown = fallback_synthesis(
            [
                {"title": "Polymer property model", "theme": "property prediction"},
                {"title": "Autonomous lab result", "theme": "autonomous labs"},
            ]
        )

        self.assertIn("### autonomous labs", markdown)
        self.assertIn("- Polymer property model", markdown)

    def test_synthesize_week_uses_model_client_and_tracks_usage(self):
        token_usage = {}
        markdown = synthesize_week(
            [{"id": "1", "title": "Polymer item", "theme": "materials AI"}],
            {"synth": {"model": "test-synth-model", "prompt": "prompts/synth.md"}},
            model_client=FakeModelClient(),
            token_usage=token_usage,
        )

        self.assertIn("Model Synthesis", markdown)
        self.assertEqual(token_usage["anthropic_synthesis"]["input_tokens"], 4)


if __name__ == "__main__":
    unittest.main()
