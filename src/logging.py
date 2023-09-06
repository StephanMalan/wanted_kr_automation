import sys
from typing import Any, Callable, Iterable

from halo import Halo
from spinners.spinners import Spinners  # type: ignore
from termcolor.termcolor import colored
from tqdm import tqdm

CHECKMARK_ICON = colored("  ✓", "light_green")
CROSS_ICON = colored("  x", "red")


class Spinner:
    load_icons = {"frames": [f"  {i}" for i in Spinners["dots"].value["frames"]]}

    def __init__(self, text: str) -> None:
        self._spinner = Halo(text=text, interval=167)
        self._spinner._spinner = self.load_icons
        self._spinner.start()

    def stop(self, text: str, successful: bool = True) -> None:
        self._spinner.stop_and_persist(CHECKMARK_ICON if successful else CROSS_ICON, text=text)


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
                log_task_success(self.success_msg.format(num=self.n))
            else:
                log_task_fail(self.error_msg)

        return _close_inner_wrapper


def log_task_success(text: str) -> None:
    print(f"{CHECKMARK_ICON} {text}")


def log_task_fail(text: str) -> None:
    print(f"{CROSS_ICON} {text}")
