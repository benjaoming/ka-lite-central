"""
Test support harness to make setup.py test work.
"""
from kalite.testing.testrunner import KALiteTestRunner


class CentralTestRunner(KALiteTestRunner):
    """Forces us to start in liveserver mode, and only includes relevant apps to test"""

    def run_tests(self, test_labels=None, **kwargs):
        """By default, only run relevant app tests.  If you specify... you're on your own!"""
        if not test_labels:  # by default, come in as empty list
            test_labels = set(['central'])

        return super(CentralTestRunner,self).run_tests(test_labels=test_labels, **kwargs)
