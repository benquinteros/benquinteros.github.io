from html.parser import HTMLParser
from pathlib import Path
import struct
import subprocess
import tempfile
import tomllib
import unittest
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
_BUILD_DIRECTORY = None
_BUILT_SITE = None


def built_site() -> Path:
    global _BUILD_DIRECTORY, _BUILT_SITE
    if _BUILT_SITE is None:
        _BUILD_DIRECTORY = tempfile.TemporaryDirectory(prefix="portfolio-site-")
        _BUILT_SITE = Path(_BUILD_DIRECTORY.name)
        result = subprocess.run(
            ["zola", "build", "--output-dir", str(_BUILT_SITE), "--force"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(
                f"Zola build failed:\n{result.stdout}\n{result.stderr}"
            )
    return _BUILT_SITE


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
        site = built_site()
        cls.home_html = (site / "index.html").read_text()
        cls.print_html = (site / "resume/print/index.html").read_text()
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
        cls.site = built_site()
        cls.home_html = (cls.site / "index.html").read_text()

    def test_source_serif_is_shipped_and_preloaded(self) -> None:
        asset = self.site / "fonts/source-serif-4-latin-wght-normal.woff2"
        self.assertTrue(asset.is_file(), "Source Serif 4 is not in the built site")
        self.assertGreater(asset.stat().st_size, 10_000)
        self.assertIn(
            "fonts/source-serif-4-latin-wght-normal.woff2", self.home_html
        )


class FaviconDeliveryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.site = built_site()
        cls.home_html = (cls.site / "index.html").read_text()

    def test_ico_fallback_precedes_the_scalable_svg_favicon(self) -> None:
        ico_reference = (
            'rel="icon" href="https://benpaternostro.com/favicon.ico" '
            'sizes="16x16 32x32"'
        )
        svg_reference = (
            'rel="icon" type="image/svg+xml" '
            'href="https://benpaternostro.com/favicon.svg" sizes="any"'
        )
        self.assertIn(svg_reference, self.home_html)
        self.assertIn(ico_reference, self.home_html)
        self.assertLess(
            self.home_html.index("favicon.ico"),
            self.home_html.index("favicon.svg"),
        )

    def test_svg_favicon_uses_the_approved_vector_geometry(self) -> None:
        svg = self.site / "favicon.svg"
        self.assertTrue(svg.is_file())
        root = ElementTree.parse(svg).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        self.assertEqual("0 0 32 32", root.attrib.get("viewBox"))
        self.assertEqual([f"{namespace}rect", f"{namespace}path"], [
            child.tag for child in root
        ])

        rect, path = root
        self.assertEqual(
            {"width": "32", "height": "32", "rx": "6", "fill": "#A33F2B"},
            rect.attrib,
        )
        self.assertEqual("#F3F0E8", path.attrib.get("fill"))
        self.assertEqual("evenodd", path.attrib.get("fill-rule"))
        self.assertEqual(
            "M7 6h10.2c4.5 0 7.2 2.1 7.2 5.7 0 2.2-1.2 3.9-3.3 4.7 "
            "2.6.7 4.1 2.4 4.1 4.7 0 3.7-2.9 5.9-7.7 5.9H7v-2.5h2V8.5H7V6Z"
            "m5.5 2.5v6.7h4.1c2.8 0 4.2-1.1 4.2-3.4 0-2.2-1.4-3.3-4.2-3.3h-4.1Z"
            "m0 9.1v6.9h4.6c2.9 0 4.4-1.1 4.4-3.5 0-2.3-1.5-3.4-4.5-3.4h-4.5Z",
            path.attrib.get("d"),
        )

    def test_ico_fallback_contains_16_and_32_pixel_png_frames(self) -> None:
        ico = self.site / "favicon.ico"
        self.assertTrue(ico.is_file())
        data = ico.read_bytes()
        self.assertEqual((0, 1, 2), struct.unpack_from("<HHH", data))

        frames = set()
        for index in range(2):
            entry = struct.unpack_from("<BBBBHHII", data, 6 + index * 16)
            width, height, _, _, _, bits_per_pixel, size, offset = entry
            width = width or 256
            height = height or 256
            self.assertEqual(32, bits_per_pixel)
            self.assertLessEqual(offset + size, len(data))
            self.assertEqual(b"\x89PNG\r\n\x1a\n", data[offset : offset + 8])
            png_width, png_height = struct.unpack_from(">II", data, offset + 16)
            self.assertEqual((width, height), (png_width, png_height))
            frames.add((width, height))

        self.assertEqual({(16, 16), (32, 32)}, frames)


class ResponsiveStyleContracts(unittest.TestCase):
    def test_body_does_not_force_a_viewport_wider_than_320px(self) -> None:
        styles = (ROOT / "static/styles.css").read_text()
        self.assertNotIn("min-width: 20rem", styles)


if __name__ == "__main__":
    unittest.main()
