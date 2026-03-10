import streamlit as st, chromadb, os
from sentence_transformers import SentenceTransformer
BASE = '/content/drive/MyDrive/EV_AI_Platform'
st.set_page_config(page_title='EV AI Diagnostics', layout='wide')
st.title('EV AI Diagnostic Assistant')
with st.sidebar:
    brand = st.selectbox('Brand',['Tesla','Nissan','Hyundai','BMW','Kia'])
    model_v = st.text_input('Model','Model 3')
    soc   = st.slider('Battery SOC %',0,100,72)
    btemp = st.slider('Battery Temp C',-10,80,34)
    dtcs  = st.text_area('Active DTC Codes',placeholder='P0A0F\nP0C6B')
    if st.button('Clear Chat'): st.session_state.msgs=[]; st.rerun()
@st.cache_resource(show_spinner='Loading model...')
def load():
    try:
        c=chromadb.PersistentClient(path=f'{BASE}/vector_db')
        col=c.get_collection('ev_manuals')
        mdl=SentenceTransformer('all-MiniLM-L6-v2')
        return col,mdl,col.count()
    except: return None,None,0
col,mdl,n=load()
st.caption(f'Knowledge Base: {n} chunks | {brand}')
if 'msgs' not in st.session_state:
    st.session_state.msgs=[{'role':'assistant','content':f'Hello! Ready to help with your {brand}.'}]
for m in st.session_state.msgs:
    with st.chat_message(m['role']): st.markdown(m['content'])
if prompt:=st.chat_input('Describe your EV problem...'):
    st.session_state.msgs.append({'role':'user','content':prompt})
    with st.chat_message('user'): st.markdown(prompt)
    with st.chat_message('assistant'):
        with st.spinner('Searching manuals...'):
            ans='Knowledge base empty — please run the embedding pipeline first.'
            if col:
                q=mdl.encode(prompt,normalize_embeddings=True).tolist()
                r=col.query(query_embeddings=[q],n_results=4)
                parts=[f'**Vehicle:** {brand} | SOC:{soc}% | Temp:{btemp}C | DTCs:{dtcs.strip() or "None"}','']
                parts.append('**From EV Knowledge Base:**')
                for i,(doc,dist) in enumerate(zip(r['documents'][0],r['distances'][0]),1):
                    parts.append(f'\n**[{i}] {(1-dist)*100:.1f}% match**\n> {doc[:300]}...')
                ans='\n'.join(parts)
        st.markdown(ans)
    st.session_state.msgs.append({'role':'assistant','content':ans})