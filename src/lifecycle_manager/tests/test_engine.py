# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0


"""Test functions for engine and executor."""
import time

from lifecycle_manager.executor.engine import Engine


class TestEngineExecutor():
    """Test class for engine and excutor."""

    def setup_method(self, method):
        """Setup method for each test."""
        self.engine = Engine('test', None)
        self.engine.executor._create_states(['FakeInit', 'FakeRun', 'FakeRunFail', 'Waiting', 'Finish', 'Fail'])
        self.engine.start()

    def teardown_method(self, method):
        """Teardown of each test."""
        self.engine.set_stop_event()
        self.engine.join()

    def test_run_engine(self):
        """Run engine and only engine."""
        assert self.engine.is_alive()
        assert not self.engine._failed
        assert not self.engine.executor.is_alive()
        assert not self.engine.process_check_thread.is_alive()

    def test_run_executor(self):
        """Run engine and executor."""
        self.engine.executor._run_params['current_state'] = 'FakeInit'
        self.engine.set_execute_event()
        time.sleep(5)
        assert self.engine.executor.is_alive()

    def test_run_executor_waiting(self):
        """Test that waiting state run properly and sets waiting flag to status."""
        self.engine.executor._run_params['current_state'] = 'Waiting'
        self.engine.set_execute_event()
        time.sleep(1)
        assert self.engine.get_executor_status() == 'Waiting'
        time.sleep(5)
        assert self.engine.get_executor_status() == 'Waiting'

    def test_waiting_game(self):
        """Test that wait sets flags and allows state change when flag set."""
        self.engine.executor._run_params['current_state'] = 'FakeInit'
        self.engine.set_execute_event()
        time.sleep(2)
        assert self.engine.get_executor_status() == 'Running'
        time.sleep(5)
        assert self.engine.get_executor_status() == 'Waiting'
        response = self.engine.set_executor_state('FakeRun')
        assert response

    def test_engine_shutdown(self):
        """Test shutdown of engine."""
        self.engine.set_stop_event()
        time.sleep(2)
        assert not self.engine.is_alive()
        assert not self.engine.executor.is_alive()

    def test_executor_fail(self):
        """Test executor fail case."""
        self.engine.executor._run_params['current_state'] = 'FakeRunFail'
        self.engine.set_execute_event()
        time.sleep(2)
        assert self.engine._failed
        assert self.engine.is_alive()

    def test_executor_backup(self):
        """Test that backup to engine is created."""
        self.engine.executor._run_params['current_state'] = 'FakeRunFail'
        self.engine.set_execute_event()
        time.sleep(2)
        assert self.engine.backup is not None

    def test_executor_restore(self):
        """Test restore of executor. This has some hacks."""
        self.engine.executor._run_params['current_state'] = 'FakeRunFail'
        self.engine.set_execute_event()
        time.sleep(2)
        self.engine.restore()
        # Rows below set the states back to test spec.
        self.engine.executor._create_states(['FakeInit', 'FakeRun', 'FakeRunFail', 'Waiting', 'Finish'])
        self.engine.executor._run_params['current_state'] = 'Waiting'
        time.sleep(2)
        assert not self.engine._failed
        assert self.engine.is_alive()
        assert self.engine.executor.is_alive()

    def test_executor_finish(self):
        """Test executor finish and shutdown."""
        self.engine.executor._run_params['current_state'] = 'Waiting'
        self.engine.set_execute_event()
        time.sleep(5)
        response = self.engine.set_executor_state('Finish')
        assert response
        time.sleep(5)
        assert self.engine.executor._run_params['finished']
        assert not self.engine._failed
        assert not self.engine.is_alive()
        assert not self.engine.executor.is_alive()
