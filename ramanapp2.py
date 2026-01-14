import io
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Raman TXT → Excel Merger", layout="wide")
st.title("Raman TXT 병합 → Excel")

# ✅ 업로더 초기화용 키(수동 제거 버튼에서만 사용)
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def clear_uploads():
    st.session_state.uploader_key += 1  # key 변경 → 업로드 목록 초기화
    st.rerun()

skiprows = st.number_input("헤더 줄 수(skiprows)", min_value=0, value=0)
wmin = st.number_input("파장 최소값", value=619.0)
wmax = st.number_input("파장 최대값", value=1724.0)

uploaded = st.file_uploader(
    "TXT 파일을 여러 개 선택하세요",
    type=["txt"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}",  # ✅ 중요
)

def read_txt(file_bytes, col_name, skiprows):
    df = pd.read_csv(
        io.BytesIO(file_bytes),
        sep=None,
        engine="python",
        skiprows=skiprows,
        header=None
    )
    df = df.iloc[:, :2].copy()
    df.columns = ["wavelength", col_name]
    return df

# ✅ 수동 제거 버튼 + 병합 버튼
if uploaded:
    col1, col2 = st.columns([1, 1])
    with col1:
        run_merge = st.button("병합 실행", type="primary")
    with col2:
        st.button("업로드 파일 전체 제거(Clear)", on_click=clear_uploads)

    if run_merge:
        merged = None
        base_wavelength = None

        for f in sorted(uploaded, key=lambda x: x.name):
            name = Path(f.name).stem
            df = read_txt(f.getvalue(), name, skiprows)

            if base_wavelength is None:
                base_wavelength = df["wavelength"].to_numpy()
                merged = df
            else:
                if not (df["wavelength"].to_numpy() == base_wavelength).all():
                    st.error("파장 축이 서로 다릅니다. skiprows/파일 형식을 확인하세요.")
                    st.stop()
                merged = merged.merge(df, on="wavelength", how="inner")

        merged = merged[(merged["wavelength"] >= wmin) & (merged["wavelength"] <= wmax)]
        merged = merged.sort_values("wavelength").reset_index(drop=True)

        st.success("병합 완료")
        st.dataframe(merged.head(30), use_container_width=True)

        out = io.BytesIO()
        merged.to_excel(out, index=False)
        out.seek(0)

        st.download_button(
            "merged.xlsx 다운로드",
            data=out.getvalue(),
            file_name="merged.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
else:
    st.caption("파일을 업로드하면 병합/제거 버튼이 나타납니다.")