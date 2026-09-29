"""EXIF, XMP, and container metadata forensic analysis."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import piexif
from PIL import Image

from app.schemas.forensics import MetadataAnalysisResult
from app.services.forensics_utils import is_image, is_pdf

MANIPULATION_TOOL_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"adobe\s*photoshop", re.I), "Adobe Photoshop"),
    (re.compile(r"\bgimp\b", re.I), "GIMP"),
    (re.compile(r"\bcanva\b", re.I), "Canva"),
    (re.compile(r"corel\s*draw", re.I), "CorelDRAW"),
    (re.compile(r"lightroom", re.I), "Adobe Lightroom"),
    (re.compile(r"affinity\s*photo", re.I), "Affinity Photo"),
    (re.compile(r"paint\.net", re.I), "Paint.NET"),
    (re.compile(r"snapseed", re.I), "Snapseed"),
    (re.compile(r"pixelmator", re.I), "Pixelmator"),
)

EXIF_DATETIME_TAGS = (
    "DateTime",
    "DateTimeOriginal",
    "DateTimeDigitized",
)


class MetadataAnalyzer:
    """Extract and evaluate metadata for manipulation indicators."""

    def analyze(self, file_path: str | Path) -> MetadataAnalysisResult:
        path = Path(file_path)
        flags: list[str] = []
        software_candidates: list[str] = []

        if is_image(path):
            image_flags, image_software = self._analyze_image(path)
            flags.extend(image_flags)
            software_candidates.extend(image_software)
        elif is_pdf(path):
            pdf_flags, pdf_software = self._analyze_pdf(path)
            flags.extend(pdf_flags)
            software_candidates.extend(pdf_software)
        else:
            flags.append(f"Unsupported file type for metadata analysis: {path.suffix}")

        software_tag, manipulation_detected = self._resolve_software_tag(software_candidates)
        if manipulation_detected:
            flags.append(f"Editing software signature detected: {software_tag}")

        return {
            "has_manipulation_tools": manipulation_detected,
            "software_tag": software_tag,
            "flags": flags,
        }

    def _analyze_image(self, path: Path) -> tuple[list[str], list[str]]:
        flags: list[str] = []
        software_candidates: list[str] = []

        with Image.open(path) as image:
            exif_data = self._extract_exif(image)
            xmp_data = self._extract_xmp(image)
            container_info = dict(image.info)

        software_candidates.extend(
            self._scan_for_software(exif_data, xmp_data, container_info)
        )
        flags.extend(self._check_timestamp_inconsistencies(exif_data))

        if path.suffix.lower() in {".jpg", ".jpeg"}:
            with Image.open(path) as image:
                if image.info.get("progressive"):
                    flags.append("Progressive JPEG encoding detected.")

        if xmp_data:
            flags.extend(self._scan_xmp_history(xmp_data))

        return flags, software_candidates

    def _analyze_pdf(self, path: Path) -> tuple[list[str], list[str]]:
        import pymupdf

        flags: list[str] = []
        software_candidates: list[str] = []

        with pymupdf.open(path) as document:
            metadata = document.metadata or {}
            xmp_xml = document.get_xml_metadata() or ""
            if document.page_count > 0:
                page = document.load_page(0)
                text_blocks = page.get_text("blocks")
                if len(text_blocks) > 0 and not metadata.get("producer"):
                    flags.append(
                        "PDF contains selectable text without producer metadata."
                    )
            if document.needs_pass:
                flags.append("PDF is encrypted or has restricted permissions.")

        normalized = {str(k).lower(): str(v) for k, v in metadata.items() if v}
        software_candidates.extend(
            self._scan_for_software(normalized, {"xmp": xmp_xml}, normalized)
        )

        creation = self._parse_pdf_date(normalized.get("creationdate", ""))
        modification = self._parse_pdf_date(normalized.get("moddate", ""))
        if creation and modification and creation > modification:
            flags.append(
                "PDF creation timestamp occurs after modification timestamp."
            )

        if xmp_xml:
            flags.extend(self._scan_xmp_history({"xmp": xmp_xml}))

        producer = normalized.get("producer", "")
        creator = normalized.get("creator", "")
        if producer or creator:
            software_candidates.extend([producer, creator])

        return flags, software_candidates

    def _extract_exif(self, image: Image.Image) -> dict[str, Any]:
        exif_dict: dict[str, Any] = {}

        try:
            raw_exif = image.info.get("exif")
            if raw_exif:
                loaded = piexif.load(raw_exif)
                for ifd_name, ifd in loaded.items():
                    if ifd_name == "thumbnail":
                        continue
                    for tag, value in ifd.items():
                        tag_name = piexif.TAGS[ifd_name][tag]["name"]
                        decoded = self._decode_exif_value(value)
                        exif_dict[tag_name] = decoded
        except Exception:
            exif_dict["exif_parse_error"] = True

        try:
            basic_exif = image.getexif()
            for tag_id, value in basic_exif.items():
                tag_name = Image.ExifTags.TAGS.get(tag_id, str(tag_id))
                exif_dict[str(tag_name)] = self._decode_exif_value(value)
        except Exception:
            pass

        return exif_dict

    def _extract_xmp(self, image: Image.Image) -> dict[str, Any]:
        xmp_data: dict[str, Any] = {}
        if hasattr(image, "getxmp"):
            try:
                raw_xmp = image.getxmp() or {}
                if isinstance(raw_xmp, dict):
                    xmp_data = raw_xmp
            except Exception:
                xmp_data["xmp_parse_error"] = True
        return xmp_data

    def _scan_for_software(
        self,
        exif_data: dict[str, Any],
        xmp_data: dict[str, Any],
        container_info: dict[str, Any],
    ) -> list[str]:
        candidates: list[str] = []
        keys_of_interest = (
            "Software",
            "ProcessingSoftware",
            "Artist",
            "HostComputer",
            "creator",
            "producer",
            "CreatorTool",
        )

        for source in (exif_data, xmp_data, container_info):
            for key, value in source.items():
                if str(key) in keys_of_interest or "software" in str(key).lower():
                    candidates.append(str(value))
                candidates.append(f"{key}={value}")

        xmp_blob = xmp_data.get("xmp")
        if isinstance(xmp_blob, str):
            candidates.append(xmp_blob)

        return candidates

    def _resolve_software_tag(
        self, candidates: list[str]
    ) -> tuple[str, bool]:
        joined = " | ".join(candidates)
        for pattern, label in MANIPULATION_TOOL_PATTERNS:
            if pattern.search(joined):
                return label, True
        return "Unknown / Not Detected", False

    def _check_timestamp_inconsistencies(self, exif_data: dict[str, Any]) -> list[str]:
        flags: list[str] = []
        parsed: dict[str, datetime] = {}

        for tag in EXIF_DATETIME_TAGS:
            raw = exif_data.get(tag)
            if not raw:
                continue
            parsed_value = self._parse_exif_datetime(str(raw))
            if parsed_value:
                parsed[tag] = parsed_value

        original = parsed.get("DateTimeOriginal")
        digitized = parsed.get("DateTimeDigitized")
        modified = parsed.get("DateTime")

        if original and digitized and original > digitized:
            flags.append("EXIF DateTimeOriginal occurs after DateTimeDigitized.")

        if original and modified and original > modified:
            flags.append("EXIF DateTimeOriginal occurs after DateTime.")

        return flags

    def _scan_xmp_history(self, xmp_data: dict[str, Any]) -> list[str]:
        flags: list[str] = []
        xmp_blob = xmp_data.get("xmp", "")
        if not isinstance(xmp_blob, str) or not xmp_blob.strip():
            return flags

        suspicious_tokens = (
            "photoshop",
            "gimp",
            "canva",
            "history",
            "derivedfrom",
            "stevt:changed",
        )
        lowered = xmp_blob.lower()
        if any(token in lowered for token in suspicious_tokens):
            flags.append("XMP history or editing workflow metadata detected.")

        try:
            root = ElementTree.fromstring(xmp_blob)
            for elem in root.iter():
                if elem.tag and "history" in elem.tag.lower():
                    flags.append("XMP document history block present.")
                    break
        except ElementTree.ParseError:
            pass

        return flags

    @staticmethod
    def _decode_exif_value(value: Any) -> Any:
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="ignore")
            except Exception:
                return value.hex()
        if isinstance(value, tuple):
            return tuple(MetadataAnalyzer._decode_exif_value(v) for v in value)
        return value

    @staticmethod
    def _parse_exif_datetime(raw: str) -> datetime | None:
        for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_pdf_date(raw: str) -> datetime | None:
        if not raw:
            return None
        cleaned = raw
        if cleaned.startswith("D:"):
            cleaned = cleaned[2:]
        cleaned = cleaned.replace("'", "")
        for fmt in (
            "%Y%m%d%H%M%S",
            "%Y%m%d%H%M%S%z",
            "%Y%m%d",
        ):
            try:
                return datetime.strptime(cleaned[: len(fmt)], fmt)
            except ValueError:
                continue
        return None
