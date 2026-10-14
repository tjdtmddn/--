from pathlib import Path
import sys

import pandas as pd
import matplotlib.pyplot as plt


CSV_PATH = Path(__file__).with_name("load_data.csv")
RESULT_PATH = Path(__file__).with_name("load_result.csv")
GRAPH_PATH = Path(__file__).with_name("load_result.png")
STRESS_GRAPH_PATH = Path(__file__).with_name("stress_plot.png")
AREA_MM2 = 100
REFERENCE_STRESS_MPA = 6
REQUIRED_COLUMNS = {"time_s", "force_N"}
VALIDATION_COLUMNS = ("time_s", "force_N")


def read_load_data(csv_path: Path) -> tuple[pd.DataFrame, list[str], int]:
    data = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    missing_columns = REQUIRED_COLUMNS - set(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"필수 열이 없습니다: {missing}")

    numeric_data = data[["time_s", "force_N"]].apply(
        pd.to_numeric, errors="coerce"
    )
    invalid_rows = numeric_data.isna().any(axis=1)
    invalid_messages = []
    for index in data.index[invalid_rows]:
        for column in VALIDATION_COLUMNS:
            if pd.isna(numeric_data.loc[index, column]):
                invalid_messages.append(
                    f"행 {index + 2}, {column} 문제값: "
                    f"{data.loc[index, column]!r}"
                )
    return (
        numeric_data.loc[~invalid_rows].reset_index(drop=True),
        invalid_messages,
        int(invalid_rows.sum()),
    )


def analyze_load_data(csv_path: Path) -> tuple[int, float, float]:
    """Return the row count, maximum load, and time of the first maximum."""
    data, _, _ = read_load_data(csv_path)
    maximum_index = data["force_N"].idxmax()

    return (
        len(data),
        float(data.loc[maximum_index, "force_N"]),
        float(data.loc[maximum_index, "time_s"]),
    )


def calculate_stress(data: pd.DataFrame, area_mm2: float) -> pd.DataFrame:
    if area_mm2 <= 0:
        raise ValueError("단면적은 0보다 커야 합니다.")

    result = data.copy()
    result["stress_MPa"] = result["force_N"] / area_mm2
    return result


def save_load_graph(data: pd.DataFrame, graph_path: Path) -> None:
    figure, force_axis = plt.subplots()
    stress_axis = force_axis.twinx()

    force_line = force_axis.plot(
        data["time_s"],
        data["force_N"],
        color="blue",
        label="force_N",
    )[0]
    stress_line = stress_axis.plot(
        data["time_s"],
        data["stress_MPa"],
        color="gold",
        label="stress_MPa",
    )[0]

    force_axis.set_xlabel("Time (s)")
    force_axis.set_ylabel("Force (N)", color="blue")
    stress_axis.set_ylabel("Stress (MPa)", color="goldenrod")
    force_axis.tick_params(axis="y", labelcolor="blue")
    stress_axis.tick_params(axis="y", labelcolor="goldenrod")
    force_axis.legend(
        [force_line, stress_line],
        [force_line.get_label(), stress_line.get_label()],
        loc="upper left",
    )
    figure.tight_layout()
    figure.savefig(graph_path)
    plt.close(figure)


def save_stress_graph(data: pd.DataFrame, graph_path: Path) -> None:
    figure, axis = plt.subplots()
    axis.plot(
        data["time_s"],
        data["stress_MPa"],
        color="gold",
        marker="o",
        linestyle="-",
    )
    maximum_index = data["stress_MPa"].idxmax()
    maximum_time = float(data.loc[maximum_index, "time_s"])
    maximum_stress = float(data.loc[maximum_index, "stress_MPa"])
    axis.scatter(
        [maximum_time],
        [maximum_stress],
        color="red",
        zorder=3,
        label="Maximum stress",
    )
    axis.annotate(
        f"{maximum_time:g} s, {maximum_stress:g} MPa",
        (maximum_time, maximum_stress),
        xytext=(8, 8),
        textcoords="offset points",
    )
    axis.set_xlabel("Time (s)")
    axis.set_ylabel("Stress (MPa)")
    axis.legend()
    figure.tight_layout()
    figure.savefig(graph_path)
    plt.close(figure)


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_PATH
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    source_data, invalid_messages, excluded_count = read_load_data(csv_path)
    for message in invalid_messages:
        print(f"제외한 행: {message} - 숫자가 아니므로 계산과 그래프에서 제외합니다.")
    if source_data.empty:
        raise ValueError("유효한 데이터가 없어 계산과 그래프 생성을 중단합니다.")

    result_data = calculate_stress(source_data, AREA_MM2)
    result_data.to_csv(RESULT_PATH, index=False)
    save_load_graph(result_data, GRAPH_PATH)
    save_stress_graph(result_data, STRESS_GRAPH_PATH)

    data_count = len(result_data)
    print(f"제외한 행 수: {excluded_count}")
    print(f"유효한 데이터 수: {data_count}")
    maximum_force_index = result_data["force_N"].idxmax()
    maximum_force = float(result_data.loc[maximum_force_index, "force_N"])
    maximum_force_time = float(result_data.loc[maximum_force_index, "time_s"])
    maximum_stress_index = result_data["stress_MPa"].idxmax()
    maximum_stress = float(result_data.loc[maximum_stress_index, "stress_MPa"])
    maximum_stress_time = float(result_data.loc[maximum_stress_index, "time_s"])
    above_reference_count = int(
        (result_data["stress_MPa"] > REFERENCE_STRESS_MPA).sum()
    )

    print(f"데이터 개수: {data_count}")
    print(f"최대 하중: {maximum_force:g} N")
    print(f"최대 하중 해당 시간: {maximum_force_time:g} s")
    print(f"최대 응력: {maximum_stress:g} MPa")
    print(f"최대 응력 해당 시간: {maximum_stress_time:g} s")
    print(
        f"기준응력 {REFERENCE_STRESS_MPA:g} MPa 초과 데이터 개수: "
        f"{above_reference_count}개"
    )


if __name__ == "__main__":
    main()
