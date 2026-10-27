import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import verify_receipts as vr

LIVE = "5420f6f0-a635-4010-a7d4-311f7cd6b0ab"
OTHER = "7e1ad17b-af99-4ae7-8c96-6783c67836d2"
FAKE = "00000000-0000-4000-8000-000000000000"
UNRELATED = "123e4567-e89b-42d3-a456-426614174000"


class TestExtract(unittest.TestCase):
    def test_all_link_forms(self):
        text = (
            f"work https://zambo.dev/run/{LIVE} and "
            f"https://zambo.dev/verify/?id={OTHER} and "
            f"https://zambo.dev/api/receipt/{FAKE}"
        )
        self.assertEqual(vr.extract_ids(text), [LIVE, OTHER, FAKE])

    def test_dupe_collapsed_and_unrelated_ignored(self):
        text = f"https://zambo.dev/run/{LIVE} https://zambo.dev/run/{LIVE} id {UNRELATED}"
        self.assertEqual(vr.extract_ids(text), [LIVE])

    def test_json_id_forms(self):
        self.assertEqual(vr.ids_from_json_text(json.dumps({"id": LIVE})), [LIVE])
        self.assertEqual(
            vr.ids_from_json_text(json.dumps({"_meta": {"dev.zambo/receipt": {"id": OTHER}}})),
            [OTHER],
        )
        self.assertEqual(vr.ids_from_json_text("not json"), [])


class FakeResp:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestVerifyId(unittest.TestCase):
    def test_verified(self):
        opener = lambda req, timeout=None: FakeResp(b'{"verification_status": "verified"}')
        self.assertEqual(vr.verify_id(LIVE, opener=opener), "verified")

    def test_not_found(self):
        def opener(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 404, "nf", None, None)

        self.assertEqual(vr.verify_id(FAKE, opener=opener), "not found")


class TestMain(unittest.TestCase):
    def run_main(self, files_text, statuses, require="false"):
        tmp = tempfile.mkdtemp()
        paths = []
        for n, text in enumerate(files_text):
            p = os.path.join(tmp, f"f{n}.md")
            with open(p, "w") as f:
                f.write(text)
            paths.append(p)
        env = {
            "INPUT_PATHS": ",".join(paths),
            "INPUT_REQUIRE_RECEIPTS": require,
            "INPUT_INCLUDE_COMMENTS": "false",
            "GITHUB_EVENT_PATH": "",
            "GH_TOKEN": "",
            "GITHUB_STEP_SUMMARY": "",
        }
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(
            vr, "verify_id", side_effect=lambda i: statuses[i]
        ), mock.patch("sys.stdout", new=io.StringIO()):
            return vr.main()

    def test_all_verified_passes(self):
        rc = self.run_main([f"see https://zambo.dev/run/{LIVE}"], {LIVE: "verified"})
        self.assertEqual(rc, 0)

    def test_one_bad_fails(self):
        rc = self.run_main(
            [f"https://zambo.dev/run/{LIVE} https://zambo.dev/run/{FAKE}"],
            {LIVE: "verified", FAKE: "not found"},
        )
        self.assertEqual(rc, 1)

    def test_none_found_require_fails(self):
        self.assertEqual(self.run_main(["no receipts here"], {}, require="true"), 1)

    def test_none_found_no_require_passes(self):
        self.assertEqual(self.run_main(["no receipts here"], {}, require="false"), 0)


if __name__ == "__main__":
    unittest.main()
