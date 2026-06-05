import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import video_to_srt


class WriteSrtTest(unittest.TestCase):
    def test_write_srt_single_keeps_existing_text(self):
        items = [
            {
                "start": 0,
                "end": 1,
                "text": "只输出一份字幕。",
                "source_text": "Source text.",
                "target_text": "Target text.",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = pathlib.Path(temp_dir) / "output.srt"
            video_to_srt.write_srt(items, output_path)

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "1\n"
                "00:00:00,000 --> 00:00:01,000\n"
                "只输出一份字幕。\n",
            )

    def test_write_srt_bilingual_keeps_source_and_target_in_one_cue(self):
        items = [
            {
                "start": 1.0,
                "end": 3.25,
                "text": "fallback",
                "source_text": "Hello world.",
                "target_text": "你好，世界。",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = pathlib.Path(temp_dir) / "output.srt"
            video_to_srt.write_srt(items, output_path, subtitle_mode="bilingual")

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "1\n"
                "00:00:01,000 --> 00:00:03,250\n"
                "Hello world.\n"
                "你好，世界。\n",
            )

    def test_bilingual_mode_requires_translate_to(self):
        with self.assertRaisesRegex(ValueError, "--translate-to"):
            video_to_srt.enrich_subtitles_with_llm(
                [{"start": 0, "end": 1, "text": "Hello."}],
                correct=False,
                translate_to=None,
                llm_model="qwen-turbo",
                subtitle_mode="bilingual",
            )


if __name__ == "__main__":
    unittest.main()
