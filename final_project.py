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
            
    def display_facility_map(self):
        st.subheader("주변 경찰서 및 소방서 위치")

        facility_map = folium.Map(location=self.map_center, zoom_start=12)

        police_stations = [
            {"name": "서울은평경찰서", "coords": [37.628283, 126.928576], "phone": "02-350-1324"},
            {"name": "서울은평경찰서 불광지구대", "coords": [37.621394, 126.926586], "phone": "02-385-9901"},
            {"name": "은평경찰서 연신내지구대", "coords": [37.615259, 126.912701], "phone": "02-350-1936"},
            {"name": "녹번파출소", "coords": [37.608834, 126.931852], "phone": "02-355-7112"},
            {"name": "서울서부경찰서", "coords": [37.602172, 126.921207], "phone": "02-335-9324"},
            {"name": "구기치안센터", "coords": [37.609558, 126.956385], "phone": "02-379-4575"},
            {"name": "서대문경찰서 홍은지구대", "coords": [37.595247, 126.946391], "phone": "02-3216-2335"},
            {"name": "정릉파출소", "coords": [37.616060, 127.008610], "phone": "02-920-1840"},
            {"name": "수유6치안센터", "coords": [37.644213, 127.015761], "phone": "02-995-9349"},
            {"name": "효자치안센터", "coords": [37.662026, 126.949243], "phone": "02-386-9561"},
            {"name": "북한산국립공원 특수산악구조대", "coords": [37.661270, 126.985093], "phone": "02-996-5306"},
            {"name": "서울경찰청802의무경찰대", "coords": [37.678546, 127.002293], "phone": "02-907-0550"},
            {"name": "의정부경찰서 호원지구대", "coords": [37.706011, 127.047858], "phone": "031-872-3425"},
            {"name": "가능지구대", "coords": [37.743398, 127.033951], "phone": "031-873-2676"},
            {"name": "부곡1리 자율방범대", "coords": [37.735401, 126.977392], "phone": "031-826-1112"},
            {"name": "장흥파출소", "coords": [37.716913, 126.940857], "phone": "031-855-5112"},
            {"name": "고양경찰서 고양파출소", "coords": [37.703420, 126.903967], "phone": "031-962-9112"}
        ]

        fire_stations = [
            {"name": "신영119안전센터", "coords": [37.605724, 126.960825], "phone": "02-391-0119"},
            {"name": "홍은119안전센터", "coords": [37.598715, 126.947020], "phone": "02-6981-5549"},
            {"name": "녹번119안전센터", "coords": [37.601088, 126.935067], "phone": "02-354-0119"},
            {"name": "삼각산119안전센터", "coords": [37.619927, 127.015545], "phone": "119"},
            {"name": "우이119안전센터", "coords": [37.640891, 127.016478], "phone": "02-904-0119"},
            {"name": "도봉소방서", "coords": [37.664118, 127.043045], "phone": "02-6981-8000"},
            {"name": "도봉119안전센터", "coords": [37.687572, 127.040911], "phone": "02-6981-8182"},
            {"name": "흥선119안전센터", "coords": [37.737062, 127.035250], "phone": "031-849-7501"},
            {"name": "장흥119지역대", "coords": [37.717949, 126.941345], "phone": "031-855-0119"},
            {"name": "은평소방서", "coords": [37.628600, 126.919772], "phone": "02-389-6119"},
            {"name": "경기도제2소방재난본부", "coords": [37.731409, 127.044048], "phone": "031-849-2960"}
        ]

        for station in police_stations:
            popup_text = f"""
            <b>{station['name']}</b><br>
            {station['phone']}
            """
            folium.Marker(
                location=station["coords"],
                popup=folium.Popup(popup_text, max_width=200),
                icon=folium.Icon(color="blue", icon="glyphicon glyphicon-star")
            ).add_to(facility_map)

        for station in fire_stations:
            popup_text = f"""
            <b>{station['name']}</b><br>
            {station['phone']}
            """
            folium.Marker(
                location=station["coords"],
                popup=folium.Popup(popup_text, max_width=200),
                icon=folium.Icon(color="red", icon="fire")
            ).add_to(facility_map)

        st_folium(facility_map, width=700, height=500)