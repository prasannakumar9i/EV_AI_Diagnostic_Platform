import streamlit as st,plotly.express as px,plotly.graph_objects as go
import pandas as pd,numpy as np
st.set_page_config(page_title='EV Fleet Analytics',layout='wide')
st.title('EV Fleet Analytics Dashboard')
np.random.seed(42); N=60
df=pd.DataFrame({'vehicle_id':[f'EV-{i:03d}' for i in range(N)],'brand':np.random.choice(['Tesla','Nissan','Hyundai','BMW'],N),'soh_pct':np.random.normal(86,9,N).clip(45,100),'soc_pct':np.random.normal(64,22,N).clip(5,100),'cycle_count':np.random.randint(40,1600,N),'fault_count':np.random.poisson(1.4,N),'risk':np.random.choice(['LOW','MEDIUM','HIGH','CRITICAL'],N,p=[0.58,0.26,0.11,0.05])})
c1,c2,c3,c4=st.columns(4)
c1.metric('Fleet Size',N)
c2.metric('Avg SOH',f"{df.soh_pct.mean():.1f}%")
c3.metric('Total Faults',int(df.fault_count.sum()))
c4.metric('High Risk',int(df.risk.isin(['HIGH','CRITICAL']).sum()))
st.plotly_chart(px.histogram(df,x='soh_pct',nbins=20,color='brand',title='SOH Distribution'),use_container_width=True)
col1,col2=st.columns(2)
rc=df.risk.value_counts()
col1.plotly_chart(go.Figure(go.Pie(labels=rc.index,values=rc.values,hole=0.4)).update_layout(title='Risk'),use_container_width=True)
col2.plotly_chart(px.scatter(df,x='cycle_count',y='soh_pct',color='risk',title='SOH vs Cycles'),use_container_width=True)
st.dataframe(df.sort_values('risk',key=lambda x:x.map({'CRITICAL':0,'HIGH':1,'MEDIUM':2,'LOW':3})),use_container_width=True)