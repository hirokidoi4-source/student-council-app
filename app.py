import glob
import os
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)


# --- 1. メインのCSVを読み込む関数（エラーが出ても止まらないようにします） ---
def get_df():
    try:
        # UTF-8かShift-JISで読み込み
        try:
            df = pd.read_csv("生徒会_年間仕事一覧.csv", encoding="utf-8")
        except:
            df = pd.read_csv("生徒会_年間仕事一覧.csv", encoding="shift_jis")

        # Googleフォーム対策：列名の空白を消して、名前にあだ名を付ける
        df.columns = df.columns.str.strip()
        name_map = {
            "月を選択してください": "列1",
            "行事名を入力してください": "行事",
            "担当学年": "担当者",
        }
        df = df.rename(columns=name_map)
        return df
    except Exception as e:
        print(f"DEBUG: CSV読み込み失敗 -> {e}")
        return pd.DataFrame()  # 空のデータを返す


# --- 🏠 TOPページ ---
@app.route("/", methods=["GET","POST"])
def index():
    df = get_df()
    if df.empty:
        return "<h1>CSVファイル『生徒会_年間仕事一覧.csv』がapp.pyと同じ場所にありません！</h1>"

    # 月のリスト（4月、5月...）を作る
    months = sorted(
        [m for m in df["列1"].unique() if isinstance(m, str) and "月" in m],
        key=lambda x: int(x.replace("月", "")),
    )
    return render_template("index.html", months=months)


# --- 📋 月の詳細ページ ---
@app.route("/view_month", methods=["POST"])
def view_month():
    selected_month = request.form.get("month_file")
    df_main = get_df()

    # ファイル探し（4月_*.csv など）
    file_list = list(
        set(
            glob.glob(f"{selected_month}_*.csv") + glob.glob(f"{selected_month}＿*.csv")
        )
    )
    all_events = []

    for file_path in file_list:
        try:
            filename = os.path.basename(file_path)
            # 行事名を抜き出す
            event_name = (
                filename.replace(".csv", "").split("_")[1].strip()
                if "_" in filename
                else filename.replace(".csv", "").split("＿")[1].strip()
            )

            # 担当者を探す
            match = df_main[df_main["行事"] == event_name]
            assigned_year = match.iloc[0]["担当者"] if not match.empty else "担当未設定"

            # 詳細CSVを読み込む
            try:
                df_detail = pd.read_csv(file_path, header=None, encoding="utf-8")
            except:
                df_detail = pd.read_csv(file_path, header=None, encoding="shift_jis")

            all_events.append(
                {
                    "name": event_name,
                    "data": df_detail.fillna("").values.tolist(),
                    "assigned": assigned_year,
                }
            )
        except Exception as e:
            print(f"DEBUG: {file_path} の読み取り中にエラー -> {e}")

    # 月の再生成
    months = sorted(
        [m for m in df_main["列1"].unique() if isinstance(m, str) and "月" in m],
        key=lambda x: int(x.replace("月", "")),
    )

    return render_template(
        "view_month.html", month=selected_month, events=all_events, months=months
    )


if __name__ == "__main__":
    app.run(debug=True, port=5002)
