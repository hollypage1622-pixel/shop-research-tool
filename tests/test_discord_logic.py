import unittest

from shop_research.discord_logic import format_summary, is_help, parse_command


class TestParseCommand(unittest.TestCase):
    def test_basic(self):
        req = parse_command("!リサーチ 札幌市中央区 カフェ")
        self.assertEqual(req.area, "札幌市中央区")
        self.assertEqual(req.industry, "カフェ")
        self.assertEqual(req.limit, 20)

    def test_with_limit_and_alt_trigger(self):
        req = parse_command("!research 大阪市北区 美容室 10")
        self.assertEqual(req.industry, "美容室")
        self.assertEqual(req.limit, 10)

    def test_limit_is_capped(self):
        req = parse_command("!リサーチ 札幌市 カフェ 999")
        self.assertEqual(req.limit, 30)

    def test_not_a_trigger(self):
        self.assertIsNone(parse_command("こんにちは"))
        self.assertIsNone(parse_command("リサーチしたい"))

    def test_missing_args_raises(self):
        with self.assertRaises(ValueError):
            parse_command("!リサーチ 札幌市中央区")

    def test_unknown_industry_raises(self):
        with self.assertRaises(ValueError):
            parse_command("!リサーチ 札幌市中央区 宇宙産業")

    def test_help(self):
        self.assertTrue(is_help("!ヘルプ"))
        self.assertFalse(is_help("!リサーチ"))


class TestFormatSummary(unittest.TestCase):
    def test_summary_counts_and_top(self):
        rows = [
            {"店名": "A店", "ランク": "S", "判定理由": "ホームページなし", "優先度スコア": 90},
            {"店名": "B店", "ランク": "C", "判定理由": "大きな課題なし", "優先度スコア": 0},
        ]
        text = format_summary("札幌市中央区", "カフェ", rows)
        self.assertIn("全2件", text)
        self.assertIn("Sランク 1件", text)
        self.assertIn("A店", text)
        self.assertNotIn("B店（", text)  # C ranks are not listed in the top section


if __name__ == "__main__":
    unittest.main()
