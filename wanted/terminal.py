from __future__ import annotations

import sys
from types import TracebackType
from typing import Any, Callable, Iterable

from halo import Halo
from spinners.spinners import Spinners  # type: ignore
from termcolor.termcolor import colored
from tqdm import tqdm

CHECKMARK_ICON = colored("✓", "light_green")
CROSS_ICON = colored("x", "red")

TASK_DEPTH = 0


def indent() -> str:
    return "  " * TASK_DEPTH


class Terminal:
    class LoadTask:
        load_icons = {"frames": [f"{indent()}{i}" for i in Spinners["dots"].value["frames"]]}

        def __init__(self, text: str) -> None:
            self._text = text
            self._running = True
            self._spinner: Halo | None = None

        def __enter__(self) -> Terminal.LoadTask:
            self._start()
            return self

        def __exit__(
            self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
        ) -> None:
            if exc_type:
                self.fail(self._text)
            if self._running:
                self.success(self._text)

        def _start(self) -> None:
            self._spinner = Halo(text=self._text, interval=167)
            self._spinner._spinner = self.load_icons  # pylint: disable=protected-access

        def _stop(self, symbol: str, text: str) -> None:
            self._running = False
            if self._spinner:
                self._spinner.stop_and_persist(symbol, text)

        def success(self, text: str) -> None:
            self._stop(f"{indent()}{CHECKMARK_ICON}", text=text)

        def fail(self, text: str) -> None:
            self._running = False
            self._stop(f"{indent()}{CROSS_ICON}", text=text)
            sys.exit(1)

    class ProgressBar(tqdm):  # type: ignore
        def __init__(
            self,
            iterable: Iterable[Any],
            desc: str,
            success_msg: str,
            error_msg: str,
            total: int | None = None,
        ):
            super().__init__(
                iterable,
                desc=desc,
                total=total,
                leave=False,
                dynamic_ncols=True,
                colour="cyan",
                bar_format="  {l_bar}{bar}| {n_fmt}/{total_fmt}",
            )
            self.close = self._close_wrapper(self.close)  # type: ignore
            self.success_msg = success_msg
            self.error_msg = error_msg

        def _close_wrapper(self, func: Callable[[], None]) -> Callable[[], None]:
            def _close_inner_wrapper() -> None:
                first_close = not self.disable
                func()
                if not first_close or any(sys.exc_info()):
                    return

                if self.n > 0:
                    Terminal.log_task_success(self.success_msg.format(num=self.n))
                else:
                    Terminal.log_task_fail(self.error_msg)

            return _close_inner_wrapper

    @staticmethod
    def log(text: str) -> None:
        print("\t" * TASK_DEPTH + text)

    @staticmethod
    def log_task_success(text: str) -> None:
        Terminal.log(f"{CHECKMARK_ICON} {text}")

    @staticmethod
    def log_task_fail(text: str) -> None:
        Terminal.log(f"{CROSS_ICON} {text}")
