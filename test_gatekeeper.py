import pytest
from gatekeeper import *


# init gatekeeper
@pytest.fixture(scope='class')
def init_gatekeeper(request):
    # get and store all cars' plates
    request.cls.l_plates = [files for subdir, dirs, files in os.walk(NOT_ALLOWED_CARS)][0]
    yield
    request.cls.l_plates = None


# Test Automatic parking lot gates controller program
@pytest.mark.usefixtures('init_gatekeeper')
class TestGatekeeper:

    def setup_method(self):
        DB(connect=True, database='public_api', user='root', password='123123', host='localhost').drop()

    def test_multi_gate_op_positive(self):
        assert ('no' in multi_gate_op(self.l_plates))

    def test_single_gate_op_positive(self):
        assert ('no' in single_gate_op(self.l_plates))

    def test_multi_gate_op_negative(self):
        assert ('yes' not in multi_gate_op(self.l_plates))

    def test_single_gate_op_negative(self):
        assert ('yes' not in single_gate_op(self.l_plates))
