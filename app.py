import streamlit as st
from final_project import ComplaintManager
from report_display import ReportViewer

st.sidebar.title("북한산 민원 신고 플랫폼")
page = st.sidebar.radio("페이지 선택", ["민원 신고", "민원 조회"])

if page == "민원 신고":
    st.title("민원 신고")
    manager = ComplaintManager()

    tab1, tab2 = st.tabs(["민원 위치 선택", "인근 구조시설 보기"])

    with tab1:
        coords = manager.render_map_input()

    with tab2:
        manager.display_facility_map()

    st.subheader("민원 정보 입력")
    author, content, submitted_date = manager.render_complaint_form()
    manager.handle_submission(author, content, submitted_date, coords)

elif page == "민원 조회":
    display = ReportViewer(None)
    display.display_complaint_map()
    display.search_section()
    display.daily_complaint_chart()
    display.display_all_data()