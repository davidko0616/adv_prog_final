import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"] 
SPREADSHEET_ID = "1AKHY2-KTT7w16Ah-4S8a0CPVyFxYzoIjGUZIy9fJVTc"
RANGE_NAME = "Sheet1"

class ReportViewer:
    def __init__(self, df=None):
        self.map_center = [37.659845, 126.992394]
        if df is not None:
            self.df = df
        else:
            self.df = self.load_sheet_data()

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

    def load_sheet_data(self):
        try:
            creds = self.authenticate_google_sheets()
            service = build("sheets", "v4", credentials=creds)
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME
            ).execute()
            values = result.get("values", [])
            if not values:
                return pd.DataFrame()
            df = pd.DataFrame(values[1:], columns=values[0])
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            return df
        except HttpError as err:
            st.error(f"Google Sheets API 오류: {err}")
            return pd.DataFrame()

    def display_complaint_map(self):
        st.subheader("신고된 민원 위치 보기")
        complaint_map = folium.Map(location=self.map_center, zoom_start=13)
        for _, row in self.df.iterrows():
            try:
                lat, lon = map(float, row["Coordinate"].strip().split(","))
                popup = f"{row['Name']} - {row['Civil Complaint']}"
                folium.Marker([lat, lon], popup=popup).add_to(complaint_map)
            except Exception as e:
                st.warning(f"좌표 변환 실패: {row['Coordinate']} → {e}")
        st_folium(complaint_map, width=700, height=500)

    def search_section(self):
        st.subheader("민원 검색")
        col1, col2 = st.columns(2)
        with col1:
            search_name = st.text_input("이름으로 검색").strip().lower()
        with col2:
            search_date = st.date_input("날짜로 검색", value=None, key="date_search")
        search_date = pd.to_datetime(search_date) if search_date else None

        filtered_df = self.df.copy()
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

    def daily_complaint_chart(self):
        st.subheader("날짜별 민원 신고 건수")
        df = self.df.dropna(subset=["Date"])
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

    def display_all_data(self):
        st.subheader("전체 민원 데이터")
        clean_df = self.df.dropna(subset=["Coordinate", "Name", "Civil Complaint"]).copy()
        st.dataframe(clean_df)