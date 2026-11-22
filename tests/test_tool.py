import unittest

from shop_research.checker import SiteCheck, detect_free_builder, parse_html_signals
from shop_research.scoring import score_lead


class TestChecker(unittest.TestCase):
    def test_detect_free_builder(self):
        self.assertEqual(detect_free_builder("https://example.jimdofree.com/"), "jimdo")
        self.assertEqual(detect_free_builder("https://example.com/"), "")
        self.assertEqual(detect_free_builder("https://foo.amebaownd.com"), "ameba-ownd")

    def test_parse_html_signals(self):
        html = """
        <html><head><title> テスト 店舗 </title>
        <meta name="viewport" content="width=device-width"></head>
        <body><a href="tel:011-000-0000">電話</a>
        <a href="https://www.instagram.com/shop/">Instagram</a>
        <footer>© 2021 Test Shop</footer></body></html>
        """
        signals = parse_html_signals(html)
        self.assertTrue(signals["has_viewport"])
        self.assertTrue(signals["has_tel_link"])
        self.assertEqual(signals["sns"], ["instagram"])
        self.assertEqual(signals["copyright_year"], 2021)
        self.assertEqual(signals["title"], "テスト 店舗")

    def test_parse_no_signals(self):
        signals = parse_html_signals("<html><body>hello</body></html>")
        self.assertFalse(signals["has_viewport"])
        self.assertEqual(signals["sns"], [])
        self.assertIsNone(signals["copyright_year"])


class TestScoring(unittest.TestCase):
    def test_no_website_is_top_priority(self):
        scored = score_lead(False, None)
        self.assertEqual(scored.rank, "S")
        self.assertIn("ホームページなし", scored.reasons)

    def test_weak_site_scores_high(self):
        check = SiteCheck(
            url="http://example.jimdofree.com",
            reachable=True,
            is_https=False,
            has_viewport=False,
            free_builder="jimdo",
            copyright_year=2020,
            has_tel_link=False,
        )
        scored = score_lead(True, check)
        self.assertGreaterEqual(scored.score, 60)
        self.assertEqual(scored.rank, "S")

    def test_healthy_site_scores_low(self):
        check = SiteCheck(
            url="https://example.com",
            reachable=True,
            is_https=True,
            has_viewport=True,
            copyright_year=2026,
            has_tel_link=True,
            sns=["instagram"],
        )
        scored = score_lead(True, check)
        self.assertEqual(scored.rank, "C")
        self.assertEqual(scored.score, 0)


if __name__ == "__main__":
    unittest.main()
