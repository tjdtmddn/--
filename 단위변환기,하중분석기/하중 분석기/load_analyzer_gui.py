from pathlib import Path
import math
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib
import pandas as pd

matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_analyzer import calculate_stress, read_load_data


DEFAULT_CSV_PATH = Path(__file__).with_name("load_data.csv")


class LoadAnalyzerGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("CSV 하중 분석기")
        self.root.geometry("800x600")
        self.root.minsize(640, 440)

        self.path_var = tk.StringVar()
        self.count_var = tk.StringVar(value="유효 데이터 수: -")
        self.section_var = tk.StringVar(value="사각형")
        self.area_var = tk.StringVar(value="단면적 A: - mm²")
        self.maximum_stress_var = tk.StringVar(value="최대 응력: -")
        self.dimension_vars: dict[str, tk.StringVar] = {}
        self.data: pd.DataFrame | None = None

        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.axis = self.figure.add_subplot(111)

        self._build_widgets()

    def _build_widgets(self) -> None:
        top_frame = ttk.Frame(self.root, padding=12)
        top_frame.pack(fill=tk.X)

        browse_button = ttk.Button(
            top_frame,
            text="CSV 찾아보기",
            command=self.select_csv_file,
        )
        browse_button.pack(side=tk.LEFT)

        path_entry = ttk.Entry(
            top_frame,
            textvariable=self.path_var,
            state="readonly",
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        count_label = ttk.Label(
            self.root,
            textvariable=self.count_var,
            padding=(12, 0, 12, 8),
        )
        count_label.pack(anchor=tk.W)

        section_frame = ttk.LabelFrame(
            self.root,
            text="단면 설정",
            padding=8,
        )
        section_frame.pack(fill=tk.X, padx=12, pady=(0, 8))

        ttk.Label(section_frame, text="단면 종류").grid(
            row=0, column=0, padx=(0, 6), pady=2
        )
        section_combobox = ttk.Combobox(
            section_frame,
            textvariable=self.section_var,
            values=("사각형", "원형봉", "원형관", "사각형관", "H형강"),
            state="readonly",
            width=10,
        )
        section_combobox.grid(row=0, column=1, padx=(0, 12), pady=2)
        section_combobox.bind("<<ComboboxSelected>>", self.update_dimension_fields)
        self.dimension_frame = ttk.Frame(section_frame)
        self.dimension_frame.grid(row=0, column=2, columnspan=5, sticky=tk.W)
        ttk.Button(
            section_frame,
            text="분석",
            command=self.analyze,
        ).grid(row=0, column=7, padx=(8, 0), pady=2)
        ttk.Label(
            section_frame,
            textvariable=self.area_var,
        ).grid(row=1, column=0, columnspan=8, sticky=tk.W, pady=(6, 0))
        ttk.Label(
            self.root,
            textvariable=self.maximum_stress_var,
            padding=(12, 0, 12, 8),
        ).pack(anchor=tk.W)

        graph_frame = ttk.LabelFrame(
            self.root,
            text="시간–응력 그래프",
            padding=8,
        )
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.update_dimension_fields(invalidate=False)

    def update_dimension_fields(
        self,
        _event: tk.Event | None = None,
        *,
        invalidate: bool = True,
    ) -> None:
        if invalidate:
            self.mark_analysis_stale()

        for child in self.dimension_frame.winfo_children():
            child.destroy()

        fields = {
            "사각형": (("폭 b (mm)", "b", "10"), ("높이 h (mm)", "h", "10")),
            "원형봉": (("지름 d (mm)", "d", "20"),),
            "원형관": (("외경 D (mm)", "D", "40"), ("두께 t (mm)", "t", "5")),
            "사각형관": (
                ("외측폭 B (mm)", "B", "40"),
                ("외측높이 H (mm)", "H", "60"),
                ("두께 t (mm)", "t", "5"),
            ),
            "H형강": (
                ("전체높이 H (mm)", "H", "100"),
                ("플랜지폭 B (mm)", "B", "80"),
                ("웨브두께 tw (mm)", "tw", "5"),
                ("플랜지두께 tf (mm)", "tf", "8"),
            ),
        }[self.section_var.get()]
        self.dimension_vars = {}
        for column, (label_text, name, default) in enumerate(fields):
            variable = tk.StringVar(value=default)
            variable.trace_add("write", self._on_dimension_changed)
            self.dimension_vars[name] = variable
            ttk.Label(self.dimension_frame, text=label_text).grid(
                row=0, column=column * 2, padx=(0, 4), pady=2
            )
            ttk.Entry(
                self.dimension_frame,
                textvariable=variable,
                width=8,
            ).grid(row=0, column=column * 2 + 1, padx=(0, 10), pady=2)

    def select_csv_file(self) -> None:
        selected_path = filedialog.askopenfilename(
            title="CSV 파일 선택",
            initialdir=str(DEFAULT_CSV_PATH.parent),
            filetypes=(("CSV 파일", "*.csv"), ("모든 파일", "*.*")),
        )
        if not selected_path:
            return

        self.load_csv(Path(selected_path))

    def load_csv(self, csv_path: Path) -> None:
        self.mark_analysis_stale()
        self.data = None
        self.count_var.set("유효 데이터 수: -")
        try:
            data, invalid_messages, _ = read_load_data(csv_path)
        except (OSError, ValueError) as error:
            messagebox.showerror("CSV 읽기 오류", str(error), parent=self.root)
            return

        self.path_var.set(str(csv_path))
        self.count_var.set(f"유효 데이터 수: {len(data)}")
        self.data = data

        if invalid_messages:
            messagebox.showwarning(
                "제외된 데이터",
                "\n".join(invalid_messages),
                parent=self.root,
            )
        if data.empty:
            messagebox.showerror(
                "분석 중단",
                "유효한 데이터가 없어 분석을 중단합니다.",
                parent=self.root,
            )

    def analyze(self) -> None:
        self.mark_analysis_stale()
        if self.data is None:
            messagebox.showerror(
                "분석 오류",
                "먼저 CSV 파일을 선택하세요.",
                parent=self.root,
            )
            return
        if self.data.empty:
            messagebox.showerror(
                "분석 중단",
                "유효한 데이터가 없어 분석을 중단합니다.",
                parent=self.root,
            )
            return

        dimension_labels = {
            "b": "폭 b",
            "h": "높이 h",
            "d": "지름 d",
            "D": "외경 D",
            "t": "두께 t",
            "B": "외측폭 B",
            "H": "외측높이 H",
            "tw": "웨브두께 tw",
            "tf": "플랜지두께 tf",
        }
        raw_dimensions = {
            name: variable.get().strip()
            for name, variable in self.dimension_vars.items()
        }
        empty_dimensions = [
            dimension_labels[name]
            for name, value in raw_dimensions.items()
            if not value
        ]
        if empty_dimensions:
            self.show_invalid_dimensions(
                f"다음 치수는 빈칸일 수 없습니다: {', '.join(empty_dimensions)}."
            )
            return

        try:
            dimensions = {
                name: float(value)
                for name, value in raw_dimensions.items()
            }
        except ValueError:
            invalid_names = [
                dimension_labels[name]
                for name, value in raw_dimensions.items()
                if not self.is_number(value)
            ]
            self.show_invalid_dimensions(
                f"숫자가 아닌 입력입니다: {', '.join(invalid_names)}."
            )
            return

        non_finite_names = [
            dimension_labels[name]
            for name, value in dimensions.items()
            if not math.isfinite(value)
        ]
        if non_finite_names:
            self.show_invalid_dimensions(
                f"유한한 숫자만 입력하세요: {', '.join(non_finite_names)}."
            )
            return

        non_positive_names = [
            dimension_labels[name]
            for name, value in dimensions.items()
            if value <= 0
        ]
        if non_positive_names:
            self.show_invalid_dimensions(
                f"0보다 큰 치수를 입력하세요: {', '.join(non_positive_names)}."
            )
            return

        section = self.section_var.get()
        if section == "사각형":
            area = dimensions["b"] * dimensions["h"]
        elif section == "원형봉":
            area = math.pi * dimensions["d"] ** 2 / 4
        elif section == "원형관":
            if 2 * dimensions["t"] >= dimensions["D"]:
                self.show_invalid_dimensions(
                    "원형관은 내부공간이 있어야 합니다. "
                    "조건 2t < D를 만족하도록 입력을 고친 뒤 다시 분석하세요."
                )
                return
            inner_diameter = dimensions["D"] - 2 * dimensions["t"]
            area = math.pi * (
                dimensions["D"] ** 2 - inner_diameter**2
            ) / 4
        elif section == "사각형관":
            if (
                2 * dimensions["t"] >= dimensions["B"]
                or 2 * dimensions["t"] >= dimensions["H"]
            ):
                self.show_invalid_dimensions(
                    "사각형관은 내부공간이 있어야 합니다. "
                    "조건 2t < B, 2t < H를 만족하도록 입력을 고친 뒤 "
                    "다시 분석하세요."
                )
                return
            area = (
                dimensions["B"] * dimensions["H"]
                - (dimensions["B"] - 2 * dimensions["t"])
                * (dimensions["H"] - 2 * dimensions["t"])
            )
        else:
            if (
                2 * dimensions["tf"] >= dimensions["H"]
                or dimensions["tw"] >= dimensions["B"]
            ):
                self.show_invalid_dimensions(
                    "H형강 치수가 겹칩니다. "
                    "조건 2tf < H, tw < B를 만족하도록 입력을 고친 뒤 "
                    "다시 분석하세요."
                )
                return
            area = (
                2 * dimensions["B"] * dimensions["tf"]
                + (dimensions["H"] - 2 * dimensions["tf"])
                * dimensions["tw"]
            )

        self.area_var.set(f"단면적 A: {area:g} mm²")
        result = calculate_stress(self.data, area)
        maximum_index = result["stress_MPa"].idxmax()
        maximum_stress = float(result.loc[maximum_index, "stress_MPa"])
        maximum_time = float(result.loc[maximum_index, "time_s"])
        self.maximum_stress_var.set(
            f"최대 응력: {maximum_stress:g} MPa (시간: {maximum_time:g} s)"
        )

        self.axis.clear()
        self.axis.plot(
            result["time_s"],
            result["stress_MPa"],
            color="gold",
            marker="o",
        )
        self.axis.set_xlabel("Time (s)")
        self.axis.set_ylabel("Stress (MPa)")
        self.axis.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()

    def _on_dimension_changed(
        self,
        _variable_name: str,
        _index: str,
        _operation: str,
    ) -> None:
        self.mark_analysis_stale()

    def mark_analysis_stale(self) -> None:
        self.area_var.set("단면적 A: 조건변경됨: 다시 분석 필요")
        self.maximum_stress_var.set("최대 응력: 조건변경됨: 다시 분석 필요")
        self.axis.clear()
        self.axis.set_xlabel("Time (s)")
        self.axis.set_ylabel("Stress (MPa)")
        self.axis.grid(True, alpha=0.3)
        self.canvas.draw_idle()

    def show_invalid_dimensions(self, message: str) -> None:
        messagebox.showerror("단면 치수 오류", message, parent=self.root)

    @staticmethod
    def is_number(value: str) -> bool:
        try:
            float(value)
        except ValueError:
            return False
        return True


def main() -> None:
    root = tk.Tk()
    LoadAnalyzerGui(root)
    root.geometry("800x600+100+100")
    root.update_idletasks()
    root.deiconify()
    root.lift()
    root.attributes("-topmost", True)
    root.update()
    root.after(500, lambda: root.attributes("-topmost", False))
    root.focus_force()
    root.mainloop()


if __name__ == "__main__":
    main()
