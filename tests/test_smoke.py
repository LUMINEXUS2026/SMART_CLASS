import unittest

from app import create_app


class SmokeTest(unittest.TestCase):
    def test_app_factory(self):
        app = create_app()
        self.assertEqual(app.name, "app")


if __name__ == "__main__":
    unittest.main()
