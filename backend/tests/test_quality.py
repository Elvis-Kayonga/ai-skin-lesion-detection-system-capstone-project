"""Unit tests for the upload quality rules (each rule on its own, then the validator that chains them)."""
import pytest
from conftest import blurry_image, jpeg_bytes, png_bytes, textured_image

from app.core.errors import ImageRejected
from app.quality import (
    BlurCheck,
    DecodableCheck,
    FileSizeCheck,
    FileTypeCheck,
    ImageValidator,
    QualityCheck,
    ResolutionCheck,
    Upload,
)

GOOD_JPEG = jpeg_bytes(textured_image())


def rejected(rule: QualityCheck, upload: Upload) -> ImageRejected:
    with pytest.raises(ImageRejected) as err:
        rule.check(upload)
    return err.value


@pytest.mark.parametrize("content_type", ["image/jpeg", "image/png"])
def test_file_type_accepts_jpeg_and_png(content_type):
    FileTypeCheck().check(Upload(content_type, GOOD_JPEG))


@pytest.mark.parametrize("content_type", ["text/plain", "image/gif", "application/pdf", None])
def test_file_type_rejects_others_with_415(content_type):
    assert rejected(FileTypeCheck(), Upload(content_type, GOOD_JPEG)).status_code == 415


def test_file_size_limit_is_inclusive():
    rule = FileSizeCheck(max_mb=1)
    rule.check(Upload("image/jpeg", b"x" * (1024 * 1024)))                      # exactly 1 MB is allowed
    assert rejected(rule, Upload("image/jpeg", b"x" * (1024 * 1024 + 1))).status_code == 413


def test_undecodable_bytes_rejected_with_400():
    assert rejected(DecodableCheck(), Upload("image/jpeg", b"garbage")).status_code == 400


@pytest.mark.parametrize("size,ok", [((224, 224), True), ((223, 400), False), ((400, 100), False)])
def test_resolution_boundary(size, ok):
    upload = Upload("image/jpeg", jpeg_bytes(textured_image(size=size)))
    if ok:
        ResolutionCheck(224).check(upload)
    else:
        assert rejected(ResolutionCheck(224), upload).status_code == 422


def test_blur_score_separates_sharp_from_blurred():
    rule = BlurCheck(threshold=5.0, side_px=512)
    assert rule.score(textured_image()) > 5.0
    assert rule.score(blurry_image()) < 5.0


def test_blur_score_does_not_depend_on_resolution():
    """The same scene at two resolutions should score about the same (it is resized to 512 px first)."""
    rule = BlurCheck(threshold=5.0, side_px=512)
    small, large = textured_image(size=(600, 450)), textured_image(size=(600, 450)).resize((2400, 1800))
    assert abs(rule.score(small) - rule.score(large)) / rule.score(small) < 0.5


def test_png_with_alpha_and_greyscale_are_converted_to_rgb():
    for img in (textured_image().convert("RGBA"), textured_image().convert("L")):
        assert Upload("image/png", png_bytes(img)).image.mode == "RGB"


def test_validator_stops_at_the_first_failing_rule():
    calls = []

    class Spy(QualityCheck):
        def __init__(self, name, fail=False):
            self.name, self.fail = name, fail

        def check(self, upload):
            calls.append(self.name)
            if self.fail:
                raise ImageRejected(self.name)

    with pytest.raises(ImageRejected):
        ImageValidator([Spy("a"), Spy("b", fail=True), Spy("c")]).validate("image/jpeg", GOOD_JPEG)
    assert calls == ["a", "b"]


def test_new_rules_can_be_added_without_changing_existing_ones():
    """Open/closed principle: a brand-new rule plugs straight into the validator."""
    class TooDark(QualityCheck):
        def check(self, upload):
            if sum(upload.image.convert("L").getdata()) / (upload.image.width * upload.image.height) < 10:
                raise ImageRejected("Image is too dark.")

    from PIL import Image
    dark = jpeg_bytes(Image.new("RGB", (300, 300), (2, 2, 2)))
    with pytest.raises(ImageRejected, match="too dark"):
        ImageValidator([FileTypeCheck(), TooDark()]).validate("image/jpeg", dark)
