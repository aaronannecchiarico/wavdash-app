import time
from unittest.mock import MagicMock, patch

import pytest

from hardware import ButtonHandler


class TestButtonHandler:
    def test_short_press_detected(self):
        on_short = MagicMock()
        on_long = MagicMock()
        handler = ButtonHandler(on_short_press=on_short, on_long_press=on_long, long_press_ms=500)

        handler.update(pressed=True, now=0.0)
        handler.update(pressed=False, now=0.2)  # Released after 200ms -> short press

        on_short.assert_called_once()
        on_long.assert_not_called()

    def test_long_press_detected(self):
        on_short = MagicMock()
        on_long = MagicMock()
        handler = ButtonHandler(on_short_press=on_short, on_long_press=on_long, long_press_ms=500)

        handler.update(pressed=True, now=0.0)
        handler.update(pressed=True, now=0.3)
        handler.update(pressed=True, now=0.6)  # Still held at 600ms -> long press fires
        handler.update(pressed=False, now=0.7)  # Release after long press — no short press

        on_long.assert_called_once()
        on_short.assert_not_called()

    def test_no_press_no_callbacks(self):
        on_short = MagicMock()
        on_long = MagicMock()
        handler = ButtonHandler(on_short_press=on_short, on_long_press=on_long)

        handler.update(pressed=False, now=0.0)
        handler.update(pressed=False, now=0.5)

        on_short.assert_not_called()
        on_long.assert_not_called()
