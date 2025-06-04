import streamlit as st
from final_project import ComplaintManager
from report_display import ReportDisplay

st.sidebar.title("북한산 민원 신고 플랫폼")
page = st.sidebar.radio("페이지 선택", ["민원 신고", "민원 조회"])

if page == "민원 신고":
    manager = ComplaintManager()
    coords = manager.render_map_input()
    author, content, date = manager.render_complaint_form()
    manager.handle_submission(author, content, date, coords)

elif page == "민원 조회":
    display = ReportDisplay(None)
    display.display_complaint_map()
    display.search_section()
    display.daily_complaint_chart()
    display.display_all_data()