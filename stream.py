import streamlit as st
import requests  # 추가!


# 1. 화면 제목
st.title("🚀 연구회 chatGPT")
st.caption("FastAPI 백엔드 + Streamlit 프론트엔드 연동")


# 2. 대화 기록을 저장할 빈 리스트 만들기 (세션 상태 활용)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. 기존 대화 기록을 화면에 쫙 뿌려주기
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])



# 기존 st.chat_input 코드를 아래처럼 수정합니다.
if prompt := st.chat_input("질문을 입력하세요..."):
    
    # 사용자가 입력한 메시지를 화면에 띄우기
    with st.chat_message("user"):
        st.markdown(prompt)

    # (여기 추가) 방금 입력한 내 질문을 금고(기록)에 저장
    st.session_state.messages.append({"role": "user", "content": prompt})

        # 4-2. AI의 답변이 들어갈 빈 공간 미리 만들기
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # 글자가 타이핑될 빈 공간
        full_response = ""               # 누적될 전체 답변
        
        # 4-3. FastAPI 서버로 스트리밍 요청 보내기 (핵심!)
        url = "http://localhost:8000/chat"
        payload = {"message": prompt, "session_id": "demo-session"}
        
        try:
            with requests.post(url, json=payload, stream=True) as response:
                response.raise_for_status()
                
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                    if chunk:
                        full_response += chunk
                        # 화면에 조각을 덧붙여서 타이핑 효과(▌) 연출
                        message_placeholder.markdown(full_response + "▌")
            
            # 스트리밍이 끝나면 깜빡이는 커서(▌) 제거
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"서버 연결 오류: {e}")
            
    # 4-4. 완성된 AI 답변을 기록에 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})