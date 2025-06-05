import os
import streamlit as st
from datetime import date
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import folium
from streamlit_folium import st_folium

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1AKHY2-KTT7w16Ah-4S8a0CPVyFxYzoIjGUZIy9fJVTc"
RANGE_NAME = "Sheet1"

class ComplaintManager:
    def __init__(self):
        self.map_center = [37.659845, 126.992394]

    def authenticate_google_sheets(self):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return creds

    def append_to_sheet(self, data_row):
        try:
            creds = self.authenticate_google_sheets()
            service = build("sheets", "v4", credentials=creds)
            sheet = service.spreadsheets()
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME,
                valueInputOption="USER_ENTERED",
                body={"values": [data_row]}
            ).execute()
        except HttpError as err:
            st.error(f"Google Sheets 저장 오류: {err}")

    def render_map_input(self):
        st.subheader("민원 위치 선택")
        interactive_map = folium.Map(location=self.map_center, zoom_start=12)
        interactive_map.add_child(folium.LatLngPopup())
        st_map = st_folium(interactive_map, width=700, height=450)
        clicked_coords = st_map.get("last_clicked", None)
        if clicked_coords:
            st.info(f"선택한 위치: 위도 {clicked_coords['lat']:.5f}, 경도 {clicked_coords['lng']:.5f}")
        return clicked_coords

    def render_complaint_form(self):
        author = st.text_input("작성자")
        content = st.text_area("민원 내용")
        submitted_date = st.date_input("작성 날짜", value=date.today())

        return author, content, submitted_date

    def handle_submission(self, author, content, submitted_date, clicked_coords):
        if st.button("신고하기"):
            if not author or not content:
                st.warning("작성자와 민원 내용을 모두 입력하세요.")
            elif not clicked_coords:
                st.warning("지도의 위치를 클릭하여 좌표를 선택하세요.")
            else:
                lat, lon = clicked_coords["lat"], clicked_coords["lng"]
                self.append_to_sheet([
                    author,
                    submitted_date.strftime("%m/%d/%Y"),
                    content,
                    f"{lat},{lon}"
                ])
                st.session_state['success_message'] = "민원이 성공적으로 저장되었습니다!"

        if 'success_message' in st.session_state:
            st.success(st.session_state['success_message'])