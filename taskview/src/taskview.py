from psutil import (
    NoSuchProcess,
    virtual_memory,
    cpu_count,
    cpu_percent,
    pids,
    Process,
)
from dashing import HSplit, VSplit, HGauge, VGauge, Text
from time import sleep
import dashing
from typing import List


class TaskView:
    def __init__(self) -> None:
        self.ui = HSplit()

    @staticmethod
    def __bytes_to_gigabyte(bytes: float) -> float:
        return bytes / 2**30

    @staticmethod
    def __colors(string: str, color: str) -> str:
        colors_list = {
            "red": "\033[0;31m{}\033[0m",
            "yellow": "\033[1;33m{}\033[0m",
            "blue": "\033[0;34m{}\033[0m",
            "magenta": "\033[0;35m{}\033[0m",
            "cyan": "\033[0;36m{}\033[0m",
            "white": "\033[1;37m{}\033[0m",
            "green": "\033[1;32m{}\033[0m",
        }

        if not color in colors_list:
            raise Exception(f"Color doesn't exist")

        return colors_list[color].format(string)

    @staticmethod
    def __percent_to_megabytes(percent: float) -> float:
        return round(
            (round(virtual_memory().total / 2**20, 2) * round(percent, 2))
            / 100,
            2,
        )

    def __memory(self) -> List[VSplit]:
        memo_iface = VSplit(VGauge(), title="Memory", border_color=3)

        ram_value = virtual_memory().percent
        memo_iface.items[0].value = ram_value
        ram_used = self.__bytes_to_gigabyte(virtual_memory().used)
        ram_total = self.__bytes_to_gigabyte(virtual_memory().total)
        memo_iface.items[0].title = (
            self.__colors(f"RAM: ", "white")
            + self.__colors(f"{ram_value} % ", "green")
            + self.__colors(f"Used: ", "white")
            + self.__colors(f"{ram_used:.2f} GB ", "green")
            + self.__colors(f"Total: {ram_total:.2f} GB", "white")
        )
        memo_iface.items[0].color = 2
        if ram_value >= 50.0:
            memo_iface.items[0].title = (
                self.__colors(f"RAM: ", "white")
                + self.__colors(f"{ram_value} % ", "yellow")
                + self.__colors(f"Used: ", "white")
                + self.__colors(f"{ram_used:.2f} GB ", "yellow")
                + self.__colors(f"Total: {ram_total:.2f} GB", "white")
            )
            memo_iface.items[0].color = 11
        if ram_value >= 80.0:
            memo_iface.items[0].title = (
                self.__colors(f"RAM: ", "white")
                + self.__colors(f"{ram_value} % ", "red")
                + self.__colors(f"Used: ", "white")
                + self.__colors(f"{ram_used:.2f} GB ", "red")
                + self.__colors(f"Total: {ram_total:.2f} GB", "white")
            )
            memo_iface.items[0].color = 1

        return [memo_iface]

    def __processor(self) -> List[VSplit]:
        processor_iface = VSplit(
            HSplit(HGauge()), HSplit(), title="Processor", border_color=2
        )

        cpu_iface = processor_iface.items[0]
        cpu_iface.title = f"CPU"
        cpu_iface.border_color = 7
        ps_cpu_percent = cpu_percent()
        cpu_iface.items[0].value = ps_cpu_percent
        cpu_iface.items[0].title = f"Usage: {ps_cpu_percent} %"
        cpu_iface.items[0].color = 2
        if ps_cpu_percent > 50.0:
            cpu_iface.items[0].color = 11
        if ps_cpu_percent > 80.0:
            cpu_iface.items[0].color = 1

        # Core block
        core_iface = processor_iface.items[1]
        cores = []
        for i in range(cpu_count()):
            cores.append(VGauge(title=f"Core[{i}]"))
        core_iface.items = cores
        cores = core_iface.items[: cpu_count()]
        ps_per_cpu = cpu_percent(percpu=True)
        for i, (core, value) in enumerate(zip(cores, ps_per_cpu)):
            core.value = value
            core.border_color = 7
            core.title = self.__colors(f"cpu[{i}]: ", "white") + self.__colors(
                f"{value} %", "green"
            )
            core.color = 2
            if value >= 50.0:
                core.title = self.__colors(f"cpu[{i}]: ", "white") + (
                    self.__colors(f"{value} %", "yellow")
                )
                core.color = 11
            if value >= 80.0:
                core.title = self.__colors(f"cpu[{i}]: ", "white") + (
                    self.__colors(f"{value} %", "red")
                )
                core.color = 1

        return [processor_iface]

    def __process(self) -> List[VSplit]:
        process_iface = VSplit(
            Text(" ", color=2), title="Process", border_color=12
        )

        process_list = []
        for id in pids():
            try:
                process_info = Process(id)
                if process_info.memory_percent() >= 0.50:
                    formated_info = {
                        "id": id,
                        "memory_percent": process_info.memory_percent(),
                        "process_name": process_info.name(),
                        "process_owner": (process_info.username()),
                    }

                    process_list.append(formated_info)
            except NoSuchProcess:
                process_list.append(
                    {
                        "id": None,
                        "memory_percent": 0.0,
                        "process_name": None,
                        "process_owner": None,
                    }
                )

        process_list = sorted(
            process_list, key=lambda x: x["memory_percent"], reverse=True
        )

        process_iface.items[0].text = " "
        for proc in process_list[:30]:
            proc_text = (
                f"{proc['id']} "
                f"{self.__percent_to_megabytes(proc['memory_percent'])} Mb "
                f"{proc['process_name']} {proc['process_owner']}\n"
            )
            process_iface.items[0].color = 2
            process_iface.items[0].text += proc_text

        return [process_iface]

    def view(self, gui: tuple) -> dashing:

        options = ["process", "processor", "memory"]

        if isinstance(gui, tuple):
            if all(x in options for x in gui) and len(gui) in range(1, 4):
                while True:
                    options = {
                        "process": self.__process(),
                        "memory": self.__memory(),
                        "processor": self.__processor(),
                    }

                    if len(gui) == 1:
                        self.ui.items = options[gui[0]]
                    if len(gui) == 2:
                        self.ui.items = options[gui[0]] + options[gui[1]]
                    if len(gui) == 3:
                        self.ui.items = (
                            options[gui[0]] + options[gui[1]] + options[gui[2]]
                        )
                    try:
                        self.ui.display()
                        sleep(0.5)
                    except KeyboardInterrupt:
                        break

