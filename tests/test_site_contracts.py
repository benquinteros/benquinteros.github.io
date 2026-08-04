from html.parser import HTMLParser
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.text_parts: list[str] = []
        self.feed(html)

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


class ResumeDataContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (ROOT / "data/resume.toml").open("rb") as source:
            cls.resume = tomllib.load(source)

    def test_editorial_positioning_is_explicit(self) -> None:
        self.assertEqual(
            self.resume["basics"].get("hero_title"),
            "Engineering across the whole delivery system.",
        )
        self.assertIn("Full-stack engineer", self.resume["basics"]["summary"])

    def test_exactly_three_roles_are_featured(self) -> None:
        featured = [
            item for item in self.resume["experience"] if item.get("featured", False)
        ]
        self.assertEqual(3, len(featured))
        self.assertTrue(
            all(item.get("featured_highlights", []) for item in featured)
        )

    def test_evidence_is_attached_to_featured_roles(self) -> None:
        evidence = [
            note
            for item in self.resume["experience"]
            if item.get("featured", False)
            for note in item.get("evidence", [])
        ]
        self.assertEqual(3, len(evidence))
        self.assertTrue(all(note["title"] and note["detail"] for note in evidence))

    def test_practice_has_three_plain_language_entries(self) -> None:
        practice = self.resume.get("practice", [])
        self.assertEqual(3, len(practice))
        self.assertTrue(all(item["title"] and item["summary"] for item in practice))


class BuiltSiteContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.home_html = (ROOT / "public/index.html").read_text()
        cls.print_html = (ROOT / "public/resume/print/index.html").read_text()
        cls.home = Document(cls.home_html)
        cls.print_document = Document(cls.print_html)

    def test_homepage_contains_editorial_sections(self) -> None:
        self.assertTrue(
            {
                "selected-record",
                "practice",
                "career-index",
                "projects",
                "toolkit",
                "background",
            }
            <= self.home.ids
        )

    def test_homepage_contains_approved_positioning(self) -> None:
        self.assertIn("Engineering across the whole delivery system.", self.home_html)
        self.assertIn("AI-assisted workflows", self.home_html)

    def test_navigation_links_to_primary_sections(self) -> None:
        self.assertTrue(
            {"#selected-record", "#practice", "#career-index"}
            <= set(self.home.links)
        )

    def test_print_resume_keeps_every_role(self) -> None:
        with (ROOT / "data/resume.toml").open("rb") as source:
            resume = tomllib.load(source)
        for item in resume["experience"]:
            self.assertIn(item["role"], self.print_document.text)


class FontDeliveryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.home_html = (ROOT / "public/index.html").read_text()

    def test_source_serif_is_shipped_and_preloaded(self) -> None:
        asset = ROOT / "public/fonts/source-serif-4-latin-wght-normal.woff2"
        self.assertTrue(asset.is_file(), "Source Serif 4 is not in the built site")
        self.assertGreater(asset.stat().st_size, 10_000)
        self.assertIn(
            "fonts/source-serif-4-latin-wght-normal.woff2", self.home_html
        )


if __name__ == "__main__":
    unittest.main()
