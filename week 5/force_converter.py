import ast
import csv
import json
import math
import operator
import tkinter as tk
from tkinter import filedialog, ttk


CATEGORIES = {
    "힘": {"N": (1, "뉴턴"), "kN": (1000, "킬로뉴턴"), "MN": (1e6, "메가뉴턴"), "kgf": (9.80665, "킬로그램힘"), "lbf": (4.4482216152605, "파운드힘")},
    "길이": {"mm": (0.001, "밀리미터"), "cm": (0.01, "센티미터"), "m": (1, "미터"), "km": (1000, "킬로미터"), "in": (0.0254, "인치"), "ft": (0.3048, "피트")},
    "질량": {"mg": (1e-6, "밀리그램"), "g": (0.001, "그램"), "kg": (1, "킬로그램"), "t": (1000, "톤"), "lb": (0.45359237, "파운드")},
    "압력": {"Pa": (1, "파스칼"), "kPa": (1000, "킬로파스칼"), "MPa": (1e6, "메가파스칼"), "bar": (1e5, "바"), "psi": (6894.757293168, "프사이")},
    "면적": {"mm²": (1e-6, "제곱밀리미터"), "cm²": (1e-4, "제곱센티미터"), "m²": (1, "제곱미터"), "km²": (1e6, "제곱킬로미터"), "in²": (0.00064516, "제곱인치"), "ft²": (0.09290304, "제곱피트")},
    "부피": {"mL": (1e-6, "밀리리터"), "L": (0.001, "리터"), "m³": (1, "세제곱미터"), "in³": (1.6387064e-5, "세제곱인치"), "ft³": (0.028316846592, "세제곱피트")},
    "속도": {"m/s": (1, "미터/초"), "km/h": (1 / 3.6, "킬로미터/시"), "mph": (0.44704, "마일/시"), "knot": (0.5144444444444444, "노트")},
    "시간": {"s": (1, "초"), "min": (60, "분"), "h": (3600, "시간"), "day": (86400, "일")},
    "에너지": {"J": (1, "줄"), "kJ": (1000, "킬로줄"), "Wh": (3600, "와트시"), "kWh": (3.6e6, "킬로와트시"), "kcal": (4184, "킬로칼로리")},
    "일률": {"W": (1, "와트"), "kW": (1000, "킬로와트"), "MW": (1e6, "메가와트"), "hp": (745.6998715822702, "마력")},
    "토크": {"N·m": (1, "뉴턴미터"), "kN·m": (1000, "킬로뉴턴미터"), "kgf·m": (9.80665, "킬로그램힘미터"), "lbf·ft": (1.3558179483314004, "파운드힘피트")},
}
TEMPERATURES = {"°C": "섭씨", "°F": "화씨", "K": "켈빈"}
SETTINGS_FILE = "calculator_settings.json"


def convert_temperature(value, source, target):
    if source not in TEMPERATURES or target not in TEMPERATURES:
        raise ValueError("지원하지 않는 온도 단위입니다.")
    celsius = value if source == "°C" else (value - 32) * 5 / 9 if source == "°F" else value - 273.15
    return celsius if target == "°C" else celsius * 9 / 5 + 32 if target == "°F" else celsius + 273.15


def convert_value(value, category, source, target):
    if category == "온도":
        return convert_temperature(value, source, target)
    units = CATEGORIES.get(category)
    if not units or source not in units or target not in units:
        raise ValueError("지원하지 않는 단위입니다.")
    return value * units[source][0] / units[target][0]


def convert_force(value, from_unit, to_unit):
    return convert_value(value, "힘", from_unit, to_unit)


def format_number(value, places, notation):
    return f"{value:.{places}e}" if notation == "과학적 표기" else f"{value:,.{places}f}"


def evaluate_expression(text, angle_mode):
    tree = ast.parse(text.replace("^", "**"), mode="eval")
    factor = math.pi / 180 if angle_mode == "DEG" else 1
    functions = {
        "sin": lambda x: math.sin(x * factor), "cos": lambda x: math.cos(x * factor),
        "tan": lambda x: math.tan(x * factor), "asin": lambda x: math.asin(x) / factor,
        "acos": lambda x: math.acos(x) / factor, "atan": lambda x: math.atan(x) / factor,
        "sqrt": math.sqrt, "log": math.log10, "ln": math.log, "abs": abs,
        "factorial": math.factorial,
    }
    constants = {"pi": math.pi, "e": math.e}
    binary = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow}
    unary = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name) and node.id in constants:
            return constants[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in binary:
            return binary[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary:
            return unary[type(node.op)](visit(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in functions and not node.keywords:
            if len(node.args) != 1:
                raise ValueError("함수는 인자 하나만 사용할 수 있습니다.")
            value = visit(node.args[0])
            if node.func.id == "factorial" and (not isinstance(value, int) or value < 0):
                raise ValueError("factorial은 0 이상의 정수만 사용할 수 있습니다.")
            return functions[node.func.id](value)
        raise ValueError("지원하지 않는 수식입니다.")

    result = visit(tree)
    if not math.isfinite(result):
        raise ValueError("결과가 유한한 숫자가 아닙니다.")
    return result


class CalculatorApp:
    def __init__(self, root):
        self.root = root
        root.title("공학용 단위 변환기")
        root.geometry("780x740")
        root.minsize(670, 620)
        self.style = ttk.Style(root)
        self.dark = False
        self.memory = 0.0
        self.conversion_result = ""
        self.expression_result = None
        self.conversion_history = []
        self.expression_history = []
        self.value = tk.StringVar()
        self.category = tk.StringVar(value="힘")
        self.source = tk.StringVar(value="kN")
        self.target = tk.StringVar(value="N")
        self.places = tk.IntVar(value=6)
        self.notation = tk.StringVar(value="일반 표기")
        self.expression = tk.StringVar()
        self.angle = tk.StringVar(value="DEG")
        self.conversion_status = tk.StringVar()
        self.expression_status = tk.StringVar()
        self.memory_text = tk.StringVar(value="메모리: 0")
        self.load_settings()
        self.build()
        self.apply_theme()
        root.bind("<Return>", self.enter)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def build(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)
        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="공학용 단위 변환기", font=("맑은 고딕", 18, "bold")).pack(side="left")
        self.theme_button = ttk.Button(header, text="어두운 테마", command=self.toggle_theme)
        self.theme_button.pack(side="right")
        self.tabs = ttk.Notebook(main)
        self.tabs.pack(fill="both", expand=True)
        self.converter_tab = ttk.Frame(self.tabs, padding=12)
        self.calculator_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.converter_tab, text="단위 변환")
        self.tabs.add(self.calculator_tab, text="공학용 계산")
        self.build_converter()
        self.build_calculator()

    def build_converter(self):
        tab = self.converter_tab
        box = ttk.LabelFrame(tab, text="변환 입력", padding=12)
        box.pack(fill="x", pady=(0, 10))
        labels = ["분야", "값", "입력 단위", "변환 단위"]
        for column, label in enumerate(labels):
            ttk.Label(box, text=label).grid(row=0, column=column, sticky="w")
        self.category_combo = ttk.Combobox(box, textvariable=self.category, values=list(CATEGORIES) + ["온도"], state="readonly", width=12)
        self.category_combo.grid(row=1, column=0, padx=(0, 8), sticky="ew")
        self.category_combo.bind("<<ComboboxSelected>>", self.category_changed)
        self.value_entry = ttk.Entry(box, textvariable=self.value, justify="right")
        self.value_entry.grid(row=1, column=1, padx=(0, 8), sticky="ew")
        self.value_entry.bind("<KeyRelease>", lambda event: self.calculate_conversion())
        self.source_combo = ttk.Combobox(box, textvariable=self.source, state="readonly", width=10)
        self.source_combo.grid(row=1, column=2, padx=(0, 8))
        self.source_combo.bind("<<ComboboxSelected>>", lambda event: self.calculate_conversion())
        self.target_combo = ttk.Combobox(box, textvariable=self.target, state="readonly", width=10)
        self.target_combo.grid(row=1, column=3)
        self.target_combo.bind("<<ComboboxSelected>>", lambda event: self.calculate_conversion())
        box.columnconfigure(1, weight=1)
        options = ttk.Frame(tab)
        options.pack(fill="x", pady=(0, 10))
        ttk.Label(options, text="소수점").pack(side="left")
        tk.Spinbox(options, from_=0, to=12, textvariable=self.places, width=5, command=self.calculate_conversion).pack(side="left", padx=(6, 16))
        ttk.Label(options, text="표기").pack(side="left")
        notation_combo = ttk.Combobox(options, textvariable=self.notation, values=["일반 표기", "과학적 표기"], state="readonly", width=12)
        notation_combo.pack(side="left", padx=6)
        notation_combo.bind("<<ComboboxSelected>>", lambda event: self.calculate_conversion())
        buttons = ttk.Frame(tab)
        buttons.pack(fill="x", pady=(0, 10))
        for text, command in [("변환", lambda: self.calculate_conversion(True)), ("단위 바꾸기", self.swap_units), ("초기화", self.clear_conversion), ("결과 복사", self.copy_conversion)]:
            ttk.Button(buttons, text=text, command=command).pack(side="left", padx=(0, 6))
        result = ttk.LabelFrame(tab, text="결과", padding=12)
        result.pack(fill="x", pady=(0, 10))
        self.result_label = ttk.Label(result, text="값을 입력하면 결과가 자동으로 계산됩니다.", font=("맑은 고딕", 12))
        self.result_label.pack(anchor="w")
        self.description = ttk.Label(result, text="")
        self.description.pack(anchor="w", pady=(6, 0))
        ttk.Label(result, textvariable=self.conversion_status, foreground="red").pack(anchor="w", pady=(6, 0))
        self.update_units()
        history = ttk.LabelFrame(tab, text="최근 변환 기록 (더블클릭하면 복원)", padding=8)
        history.pack(fill="both", expand=True)
        self.conversion_list = tk.Listbox(history, height=8)
        self.conversion_list.pack(side="left", fill="both", expand=True)
        self.conversion_list.bind("<Double-Button-1>", self.load_conversion)
        scroll = ttk.Scrollbar(history, command=self.conversion_list.yview)
        scroll.pack(side="right", fill="y")
        self.conversion_list.config(yscrollcommand=scroll.set)
        history_buttons = ttk.Frame(tab)
        history_buttons.pack(fill="x", pady=(6, 0))
        ttk.Button(history_buttons, text="CSV로 저장", command=self.export_conversion_history).pack(side="left")
        ttk.Button(history_buttons, text="변환 기록 전체 삭제", command=self.clear_conversion_history).pack(side="right")

    def build_calculator(self):
        tab = self.calculator_tab
        self.calculator_panel = tk.Frame(tab, bg="#20262b")
        self.calculator_panel.pack(fill="x")

        display_frame = tk.Frame(self.calculator_panel, bg="#11161a", padx=14, pady=12)
        display_frame.pack(fill="x", pady=(0, 12))
        mode_row = tk.Frame(display_frame, bg="#11161a")
        mode_row.pack(fill="x")
        tk.Label(mode_row, text="SCIENTIFIC", bg="#11161a", fg="#68d7ca", font=("Consolas", 9, "bold")).pack(side="left")
        self.angle_buttons = {}
        for mode in ("DEG", "RAD"):
            button = tk.Button(mode_row, text=mode, command=lambda value=mode: self.set_angle(value), width=4, relief="flat", bd=0, font=("Consolas", 9, "bold"))
            button.pack(side="right", padx=(4, 0))
            self.angle_buttons[mode] = button
        self.expression_entry = tk.Entry(display_frame, textvariable=self.expression, justify="right", font=("Consolas", 24), relief="flat", bd=0)
        self.expression_entry.pack(fill="x", pady=(12, 3), ipady=7)
        self.expression_entry.bind("<KeyRelease>", lambda event: self.calculate_expression())
        self.expression_label = tk.Label(display_frame, text="", anchor="e", bg="#11161a", fg="#94a3ad", font=("Consolas", 14))
        self.expression_label.pack(fill="x")
        tk.Label(display_frame, textvariable=self.expression_status, anchor="e", bg="#11161a", fg="#ff8b8b", font=("맑은 고딕", 9)).pack(fill="x", pady=(4, 0))

        memory = tk.Frame(self.calculator_panel, bg="#20262b")
        memory.pack(fill="x", pady=(0, 10))
        tk.Label(memory, textvariable=self.memory_text, bg="#20262b", fg="#aab5bd", font=("Consolas", 10)).pack(side="left")
        for text, command in [("MC", self.memory_clear), ("MR", self.memory_recall), ("M+", self.memory_add), ("M-", self.memory_subtract)]:
            self.make_calculator_button(memory, text, command, "memory", width=4).pack(side="right", padx=(5, 0))

        keypad = tk.Frame(self.calculator_panel, bg="#20262b")
        keypad.pack(fill="x", pady=(0, 12))
        key_rows = [
            [("sin", "sin(", "function"), ("cos", "cos(", "function"), ("tan", "tan(", "function"), ("log", "log(", "function"), ("ln", "ln(", "function")],
            [("√", "sqrt(", "function"), ("x²", "**2", "function"), ("(", "(", "function"), (")", ")", "function"), ("π", "pi", "function")],
            [("7", "7", "number"), ("8", "8", "number"), ("9", "9", "number"), ("÷", "/", "operator"), ("C", "C", "danger")],
            [("4", "4", "number"), ("5", "5", "number"), ("6", "6", "number"), ("×", "*", "operator"), ("DEL", "DEL", "operator")],
            [("1", "1", "number"), ("2", "2", "number"), ("3", "3", "number"), ("−", "-", "operator"), ("%", "%", "operator")],
            [("0", "0", "number"), (".", ".", "number"), ("+", "+", "operator"), ("^", "**", "operator"), ("=", "=", "equals")],
        ]
        for row_index, row in enumerate(key_rows):
            for column_index, (label, value, kind) in enumerate(row):
                button = self.make_calculator_button(keypad, label, lambda value=value: self.calculator_key(value), kind)
                button.grid(row=row_index, column=column_index, sticky="nsew", padx=3, pady=3, ipady=7)
            keypad.rowconfigure(row_index, weight=1)
        for column_index in range(5):
            keypad.columnconfigure(column_index, weight=1)

        utility_row = tk.Frame(self.calculator_panel, bg="#20262b")
        utility_row.pack(fill="x", pady=(0, 10))
        self.make_calculator_button(utility_row, "초기화", self.clear_expression, "utility").pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.make_calculator_button(utility_row, "결과 복사", self.copy_expression, "utility").pack(side="left", fill="x", expand=True, padx=4)
        self.make_calculator_button(utility_row, "CSV 저장", self.export_expression_history, "utility").pack(side="left", fill="x", expand=True, padx=4)
        self.make_calculator_button(utility_row, "기록 삭제", self.clear_expression_history, "utility").pack(side="left", fill="x", expand=True, padx=(4, 0))

        history = ttk.LabelFrame(tab, text="계산 기록 (더블클릭하면 복원)", padding=8)
        history.pack(fill="both", expand=True)
        self.expression_list = tk.Listbox(history, height=8)
        self.expression_list.pack(side="left", fill="both", expand=True)
        self.expression_list.bind("<Double-Button-1>", self.load_expression)
        scroll = ttk.Scrollbar(history, command=self.expression_list.yview)
        scroll.pack(side="right", fill="y")
        self.expression_list.config(yscrollcommand=scroll.set)

    def make_calculator_button(self, parent, text, command, kind, width=None):
        colors = {
            "number": ("#30383f", "#f1f5f7", "#3c464e"),
            "function": ("#3d4656", "#b9e6df", "#4d596b"),
            "operator": ("#45566a", "#f6d58c", "#566c83"),
            "equals": ("#1fae9d", "#ffffff", "#2bc8b5"),
            "danger": ("#563d45", "#ffb5b5", "#704c56"),
            "memory": ("#283137", "#9ed8d1", "#35434a"),
            "utility": ("#283137", "#c7d0d5", "#35434a"),
        }
        background, foreground, active = colors[kind]
        options = {"text": text, "command": command, "bg": background, "fg": foreground, "activebackground": active, "activeforeground": "white", "relief": "flat", "bd": 0, "font": ("맑은 고딕", 10, "bold"), "cursor": "hand2"}
        if width:
            options["width"] = width
        return tk.Button(parent, **options)

    def calculator_key(self, value):
        if value == "C":
            self.clear_expression()
        elif value == "DEL":
            self.expression.set(self.expression.get()[:-1])
            self.calculate_expression()
        elif value == "=":
            self.calculate_expression_and_record()
        else:
            self.expression_entry.insert(tk.END, value)
            self.calculate_expression()

    def set_angle(self, mode):
        self.angle.set(mode)
        self.calculate_expression()

    def update_units(self):
        units = list(TEMPERATURES if self.category.get() == "온도" else CATEGORIES[self.category.get()])
        self.source_combo.config(values=units)
        self.target_combo.config(values=units)
        if self.source.get() not in units:
            self.source.set(units[0])
        if self.target.get() not in units or self.target.get() == self.source.get():
            self.target.set(units[1] if len(units) > 1 else units[0])
        self.update_description()

    def update_description(self):
        if self.category.get() == "온도":
            name = TEMPERATURES.get(self.target.get(), "")
        else:
            name = CATEGORIES[self.category.get()].get(self.target.get(), (0, ""))[1]
        self.description.config(text=f"변환 단위 설명: {name}")

    def category_changed(self, event=None):
        self.update_units()
        self.calculate_conversion()

    def calculate_conversion(self, record=False):
        self.conversion_status.set("")
        text = self.value.get().strip()
        if not text:
            self.result_label.config(text="값을 입력하면 결과가 자동으로 계산됩니다.")
            return
        try:
            value = float(text)
            if not math.isfinite(value):
                raise ValueError("NaN과 무한대는 사용할 수 없습니다.")
            places = int(self.places.get())
            if not 0 <= places <= 12:
                raise ValueError("소수점 자리 수는 0에서 12 사이여야 합니다.")
            result = convert_value(value, self.category.get(), self.source.get(), self.target.get())
            self.conversion_result = f"{format_number(result, places, self.notation.get())} {self.target.get()}"
            self.result_label.config(text=self.conversion_result)
            self.update_description()
            if record:
                item = {"category": self.category.get(), "value": text, "source": self.source.get(), "target": self.target.get(), "text": f"{value:g} {self.source.get()} = {self.conversion_result}"}
                self.conversion_history.insert(0, item)
                self.conversion_list.insert(0, item["text"])
        except (ValueError, OverflowError, ZeroDivisionError, tk.TclError) as error:
            self.conversion_result = ""
            self.result_label.config(text="")
            self.conversion_status.set(str(error))

    def swap_units(self):
        source = self.source.get()
        self.source.set(self.target.get())
        self.target.set(source)
        self.calculate_conversion()

    def clear_conversion(self):
        self.value.set("")
        self.category.set("힘")
        self.update_units()
        self.source.set("kN")
        self.target.set("N")
        self.places.set(6)
        self.notation.set("일반 표기")
        self.conversion_result = ""
        self.result_label.config(text="값을 입력하면 결과가 자동으로 계산됩니다.")
        self.conversion_status.set("")
        self.value_entry.focus()

    def copy_conversion(self):
        if not self.conversion_result:
            self.conversion_status.set("먼저 변환을 실행하세요.")
            return
        text = f"{self.value.get().strip()} {self.source.get()} = {self.conversion_result}"
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.conversion_status.set("전체 결과를 클립보드에 복사했습니다.")

    def load_conversion(self, event=None):
        selected = self.conversion_list.curselection()
        if not selected:
            return
        item = self.conversion_history[selected[0]]
        self.category.set(item["category"])
        self.update_units()
        self.value.set(item["value"])
        self.source.set(item["source"])
        self.target.set(item["target"])
        self.calculate_conversion()

    def clear_conversion_history(self):
        self.conversion_history.clear()
        self.conversion_list.delete(0, tk.END)

    def export_conversion_history(self):
        if not self.conversion_history:
            self.conversion_status.set("저장할 변환 기록이 없습니다.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["분야", "값", "입력 단위", "변환 단위", "결과"])
            for item in self.conversion_history:
                writer.writerow([item["category"], item["value"], item["source"], item["target"], item["text"]])
        self.conversion_status.set("변환 기록을 CSV 파일로 저장했습니다.")

    def calculate_expression(self):
        self.expression_status.set("")
        text = self.expression.get().strip()
        if not text:
            self.expression_result = None
            self.expression_label.config(text="")
            return
        try:
            self.expression_result = evaluate_expression(text, self.angle.get())
            self.expression_label.config(text=format_number(self.expression_result, int(self.places.get()), self.notation.get()))
        except (ValueError, SyntaxError, TypeError, OverflowError, ZeroDivisionError) as error:
            self.expression_result = None
            self.expression_label.config(text="")
            self.expression_status.set(f"수식 오류: {error}")

    def calculate_expression_and_record(self):
        self.calculate_expression()
        if self.expression_result is not None:
            text = f"{self.expression.get().strip()} = {self.expression_label.cget('text')}"
            self.expression_history.insert(0, {"expression": self.expression.get(), "text": text})
            self.expression_list.insert(0, text)

    def clear_expression(self):
        self.expression.set("")
        self.expression_result = None
        self.expression_label.config(text="")
        self.expression_status.set("")

    def copy_expression(self):
        if self.expression_result is None:
            self.expression_status.set("먼저 수식을 계산하세요.")
            return
        text = f"{self.expression.get().strip()} = {self.expression_label.cget('text')}"
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.expression_status.set("결과를 클립보드에 복사했습니다.")

    def load_expression(self, event=None):
        selected = self.expression_list.curselection()
        if selected:
            self.expression.set(self.expression_history[selected[0]]["expression"])
            self.calculate_expression()

    def clear_expression_history(self):
        self.expression_history.clear()
        self.expression_list.delete(0, tk.END)

    def export_expression_history(self):
        if not self.expression_history:
            self.expression_status.set("저장할 계산 기록이 없습니다.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["수식", "결과"])
            for item in self.expression_history:
                writer.writerow([item["expression"], item["text"]])
        self.expression_status.set("계산 기록을 CSV 파일로 저장했습니다.")

    def memory_clear(self):
        self.memory = 0.0
        self.memory_text.set("메모리: 0")

    def memory_recall(self):
        self.expression.set(f"{self.memory:.15g}")
        self.calculate_expression()

    def memory_add(self):
        if self.expression_result is not None:
            self.memory += self.expression_result
            self.memory_text.set(f"메모리: {self.memory:.12g}")

    def memory_subtract(self):
        if self.expression_result is not None:
            self.memory -= self.expression_result
            self.memory_text.set(f"메모리: {self.memory:.12g}")

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as file:
                settings = json.load(file)
            category = settings.get("category")
            if category in list(CATEGORIES) + ["온도"]:
                self.category.set(category)
            if isinstance(settings.get("source"), str):
                self.source.set(settings["source"])
            if isinstance(settings.get("target"), str):
                self.target.set(settings["target"])
            places = settings.get("places")
            if isinstance(places, int) and 0 <= places <= 12:
                self.places.set(places)
            if settings.get("notation") in ("일반 표기", "과학적 표기"):
                self.notation.set(settings["notation"])
            if settings.get("angle") in ("DEG", "RAD"):
                self.angle.set(settings["angle"])
            self.dark = bool(settings.get("dark", self.dark))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass

    def save_settings(self):
        settings = {
            "category": self.category.get(),
            "source": self.source.get(),
            "target": self.target.get(),
            "places": self.places.get(),
            "notation": self.notation.get(),
            "angle": self.angle.get(),
            "dark": self.dark,
        }
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump(settings, file, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def close(self):
        self.save_settings()
        self.root.destroy()

    def enter(self, event=None):
        if self.tabs.index(self.tabs.select()) == 0:
            self.calculate_conversion(True)
        else:
            self.calculate_expression_and_record()

    def toggle_theme(self):
        self.dark = not self.dark
        self.apply_theme()

    def apply_theme(self):
        background, foreground, field = (("#202124", "#f1f3f4", "#303134") if self.dark else ("#f4f6f8", "#202124", "white"))
        self.root.configure(background=background)
        self.theme_button.config(text="밝은 테마" if self.dark else "어두운 테마")
        self.style.configure("TFrame", background=background)
        self.style.configure("TLabel", background=background, foreground=foreground)
        self.style.configure("TLabelframe", background=background, foreground=foreground)
        self.style.configure("TLabelframe.Label", background=background, foreground=foreground)
        self.style.configure("TNotebook", background=background)
        self.style.configure("TNotebook.Tab", background=field, foreground=foreground)
        self.style.configure("TEntry", fieldbackground=field, foreground=foreground)
        self.style.configure("TCombobox", fieldbackground=field, foreground=foreground)
        self.conversion_list.config(background=field, foreground=foreground)
        self.expression_list.config(background=field, foreground=foreground)


def main():
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
