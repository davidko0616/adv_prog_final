import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

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
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        if not values:
            st.error("Google Sheet에서 데이터를 찾을 수 없습니다.")
            return pd.DataFrame()

        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except HttpError as err:
        st.error(f"Google Sheets API 오류: {err}")
        return pd.DataFrame()

st.title("북한산 민원 신고 플랫폼")
df = load_sheet_data()

if df.empty:
    st.stop()

df.dropna(subset=["Coordinate", "Name", "Civil Complaint"], inplace=True)


st.dataframe(df)

m = folium.Map(location=[37.659845, 126.992394], zoom_start=13)

for _, row in df.iterrows():
    try:
        coord = row["Coordinate"].strip()
        lat, lon = map(float, coord.strip().split(","))
        popup = f"{row['Name']} - {row['Civil Complaint']}"
        folium.Marker([lat, lon], popup=popup).add_to(m)
    except Exception as e:
        st.warning(f"좌표 변환 실패: {row['Coordinate']} → {e}")

st_folium(m, width=700, height=500)

search_name = st.text_input("이름으로 검색하세요").strip().lower()

if search_name:
    filtered_df = df[df["Name"].str.lower().str.contains(search_name)]
    if filtered_df.empty:
        st.info("해당 이름이 포함된 신고자를 찾을 수 없습니다.")
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
    st.info("이름을 입력해 검색하세요.")

print("check check")