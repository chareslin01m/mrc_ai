"""
EduChat Backend - 교육용 초간단 버전
핵심 로직: FastAPI + LangChain 연동 및 스트리밍
"""
import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 1. 환경 변수 로드 (API 키 등)
load_dotenv()

# 2. FastAPI 웹 서버 생성
app = FastAPI(title="EduChat Simple API")

# 프론트엔드 통신을 위한 필수 설정 (설명 생략 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)




# ─── LangChain 설정 ───────────────────────────────────────

# 3. LLM 세팅
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0.7,
)

# 4. Prompt 세팅 - 'history'라는 빈 공간을 미리 파놓음
prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 친절한 AI 어시스턴트입니다."),
    MessagesPlaceholder(variable_name="history"), 
    ("human", "{input}"),
])

# 5.LCEL 파이프라인
chain = prompt | llm | StrOutputParser()

# 6. 기억력(Memory) 장착 - 세션별로 대화 내역 저장
session_store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]

# 파이프라인(chain)에 대화 내역(History) 자동 주입 기능 추가
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)







# ─── API 엔드포인트 ───────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

# 7. 메인 채팅 엔드포인트 및 실시간 전송(Streaming)
@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        
        # .astream()을 통해 생성되는 단어(chunk)들을 실시간으로 계속 밀어냄(yield)
        async for chunk in chain_with_history.astream(
            {"input": req.message},
            config={"configurable": {"session_id": req.session_id}}
        ):
            yield chunk

    # StreamingResponse로 묶어서 브라우저로 실시간 전송
    return StreamingResponse(generate(), media_type="text/plain")

