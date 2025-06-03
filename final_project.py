import streamlit as st
import pandas as pd
import folium
import os
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1AKHY2-KTT7w16Ah-4S8a0CPVyFxYzoIjGUZIy9fJVTc"
RANGE_NAME = "Sheet1"

def load_sheet_data():
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
    
    try:
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        if not values:
            st.error("Google Sheet에서 데이터를 찾을 수 없습니다.")
            return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except HttpError as err:
        st.error(f"Google Sheets API 오류: {err}")
        return pd.DataFrame()

def append_to_sheet(data_row):
    try:
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

class Complaint:
    def __init__(self, author, content, coordinates, submitted_date):
        self.author = author
        self.content = content
        self.coordinates = coordinates
        self.submitted_date = submitted_date

    def __str__(self):
        return f""" Complaint by {self.author} on {self.submitted_date}:
        Location: {self.coordinates}
        Content: {self.content}"""

st.title("북한산 민원 신고 플랫폼")
df = load_sheet_data()
if df.empty:
    st.stop()

df["Date"] = pd.to_datetime(df.get("Date"), errors="coerce")

st.subheader("기존 민원 위치")
map_center = [37.659845, 126.992394]
complaint_map = folium.Map(location=map_center, zoom_start=13)

for _, row in df.iterrows():
    try:
        lat, lon = map(float, row["Coordinate"].strip().split(","))
        popup = f"{row['Name']} - {row['Civil Complaint']}"
        folium.Marker([lat, lon], popup=popup).add_to(complaint_map)
    except Exception as e:
        st.warning(f"좌표 변환 실패: {row['Coordinate']} → {e}")

st_folium(complaint_map, width=700, height=500)

st.subheader("사당 위치를 클릭해서 민원 등록록")
interactive_map = folium.Map(location=map_center, zoom_start=13)
interactive_map.add_child(folium.LatLngPopup())
click_data = st_folium(interactive_map, width=700, height=500)
clicked_coords = click_data.get("last_clicked") if click_data else None

if clicked_coords:
    st.success(f"선택한 위치: 위도 {clicked_coords['lat']}, 경도 {clicked_coords['lng']}")

st.subheader("민원 정보 입력력")
author = st.text_input("작성자")
content = st.text_area("민원 내용")
submitted_date = st.date_input("작성 날짜", value=date.today())

if st.button("신고하기"):
    if clicked_coords:
        lat, lon = clicked_coords["lat"], clicked_coords["lng"]
        complaint = Complaint(author, content, (lat, lon), submitted_date)
        append_to_sheet([
            author,
            submitted_date.strftime("%Y-%m-%d"),
            content,
            f"{lat},{lon}"
        ])
        st.success("민원이 성공적으로 저장되었습니다!")
        st.text(str(complaint))
    else:
        st.warning("지도의 위치를 클릭하세요.")

# yaejun part

map_center = [37.659845, 126.992394]
m = folium.Map(location=map_center, zoom_start=13)

for _, row in df.iterrows():
    try:
        lat, lon = map(float, row["Coordinate"].strip().split(","))
        popup = f"{row['Name']} - {row['Civil Complaint']}"
        folium.Marker([lat, lon], popup=popup).add_to(m)
    except Exception as e:
        st.warning(f"좌표 변환 실패: {row['Coordinate']} → {e}")

map_data = st_folium(m, width=700, height=500)

st.subheader("민원 검색")
col1, col2 = st.columns(2)
with col1:
    search_name = st.text_input("이름으로 검색").strip().lower()
with col2:
    search_date = st.date_input("날짜로 검색", value=None, key="date_search")
search_date = pd.to_datetime(search_date) if search_date else None

filtered_df = df.copy()
if search_name:
    filtered_df = filtered_df[filtered_df["Name"].str.lower().str.contains(search_name)]
if search_date:
    filtered_df = filtered_df[filtered_df["Date"].dt.date == search_date.date()]

if search_name or search_date:
    if filtered_df.empty:
        st.warning("검색 조건에 해당하는 데이터가 없습니다.")
    else:
        st.subheader("검색 결과")
        for _, row in filtered_df.iterrows():
            st.markdown(f"""
            이름: {row['Name']}  
            날짜: {row.get('Date', '정보 없음')}  
            신고 내용: {row.get('Civil Complaint', '정보 없음')}  
            좌표: {row.get('Coordinate', '정보 없음')}  
            ---  
            """)
else:
    st.info("이름 또는 날짜 중 하나를 입력하여 검색하세요.")

st.subheader("날짜별 민원 신고 건수")
df = df.dropna(subset=["Date"])
complaint_by_day = df["Date"].dt.date.value_counts().sort_index()

if not complaint_by_day.empty:
    plt.figure(figsize=(10, 4))
    sns.barplot(x=complaint_by_day.index.astype(str), y=complaint_by_day.values, color="salmon")
    plt.xlabel("날짜")
    plt.ylabel("민원 건수")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)
else:
    st.warning("날짜 정보가 누락되어 그래프를 표시할 수 없습니다.")

st.subheader("전체 민원 데이터")
df.dropna(subset=["Coordinate", "Name", "Civil Complaint"], inplace=True)
st.dataframe(df)