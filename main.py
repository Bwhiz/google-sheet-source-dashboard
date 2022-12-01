import streamlit as st
from shillelagh.backends.apsw.db import connect
import shillelagh
import pandas as pd
import plotly.express as px


st.set_page_config(
    page_title="Employee Dashboard",
    page_icon="📊",
    layout = 'wide'  
)

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>',unsafe_allow_html=True)

# ------------ {connection} --------------------------
@st.cache(allow_output_mutation=True)
def get_database_connection():
    return connect(":memory:")

conn = get_database_connection()

@st.cache(ttl=600, hash_funcs={shillelagh.backends.apsw.db.Connection: hash})
def run_query(query, connection):
    df = pd.read_sql(query,connection)
    return df
# --------------------------------------------------------------
sheet_url = st.secrets["public_gsheets_url"]
data = run_query(f"""select * from "{sheet_url}";""", conn)

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

#st.markdown("<h2 style='text-align: center;'>Employee Dashboard </h2>", unsafe_allow_html=True)

file = data.drop_duplicates(subset='EEID') #dropping duplicate employee ID
file['salary_cleaned'] = file['Annual Salary'].astype('str').str.strip().str.replace('$','').str.replace(',','').astype('float64')
file['iso_country'] = file['Country'].map({'United States': 'USA',
                                           'China': 'CHN',
                                           'Brazil': 'BRA'})

kp1, kp2, kp3, kp4 = st.columns(4)
no_of_employees = len(file)
avg_salary = human_format(round(file['salary_cleaned'].mean(), 2))
perc_of_women = round(len(file[file['Gender']=='Female'])/len(file) * 100, 2)
no_of_biz_unit = file['Business Unit'].nunique()
with kp1:
    st.metric(label = "Number of Employees", value=no_of_employees)
kp2.metric(label = "Avg Salary", value = f'${avg_salary}')
kp3.metric(label = "Ratio of Female Employees", value = '{:0.2f}%'.format(perc_of_women))
kp4.metric(label = "Number of business  Units", value = no_of_biz_unit)

st.header("")

kp5, kp6 = st.columns([1,2])

with kp5:
    fig = px.bar(file['Department'].value_counts(), text='value',
       labels={'value':'# of Employees', 'index':''})
    fig.update_traces(marker_color='darkblue',textposition='outside')
    fig.update_layout(width=800, height=500, bargap=0.05,plot_bgcolor='rgba(0, 0, 0, 0)',paper_bgcolor='rgba(0, 0, 0, 0)',showlegend=False, title_text='Employees by Department', title_x=0.5)
    st.plotly_chart(fig, use_container_width=True)
    
with kp6:
    fig = px.choropleth(file['iso_country'].value_counts().to_frame().reset_index(), locations='index', color='iso_country',
                    labels= {'index':'Country',
                             'iso_country':'# of employees'})
    fig.update_layout(width=800, height=500,plot_bgcolor='#FFFFFF',paper_bgcolor='rgba(0, 0, 0, 0)',showlegend=False, title_text='Number of Employees by Country', title_x=0.5,geo_bgcolor='rgba(0, 0, 0, 0)')
    st.plotly_chart(fig, use_container_width=True)
    
