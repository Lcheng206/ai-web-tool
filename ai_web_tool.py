import streamlit as st
import requests
import json

# -------------------------- 核心配置（你的智谱信息，不用改） --------------------------
API_KEY = "e5f5f77520db4c1fb1298ff8006ce6f5.ZZjfpgRXAqbqBOyz"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL_NAME = "glm-4.5-flash"

# 全局Session复用TCP连接
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept-Encoding": "gzip, deflate"
})

# -------------------------- Streamlit 页面配置+美化 --------------------------
st.set_page_config(page_title="专属人设AI助手", page_icon="✨", layout="wide")
st.markdown("""
<style>
    .main {background-color: #f7f9fc;}
    .stChatMessage {border-radius: 12px; padding:8px;}
</style>
""", unsafe_allow_html=True)

st.title("✨ 我的专属人设AI助手")
st.divider()

# ========== 侧边栏：人设设置面板 ==========
with st.sidebar:
    st.header("⚙️ AI人设设置")
    # 预设角色
    role_choice = st.selectbox(
        "选择AI身份",
        ["通用智能助手", "幽默聊天搭子", "专业文案写手", "学习答疑老师", "职场顾问", "自定义人设"]
    )

    # 预设系统提示词
    role_prompt_dict = {
        "通用智能助手": "你是友好、简洁、专业的AI助手，回答通俗易懂。",
        "幽默聊天搭子": "你是风趣幽默、爱开玩笑的聊天搭子，语气轻松活泼。",
        "专业文案写手": "你是高级文案师，擅长写朋友圈、文案、标题，简洁高级。",
        "学习答疑老师": "你是耐心的学习老师，讲解细致，举例通俗。",
        "职场顾问": "你是资深职场顾问，给出实用、落地的职场建议。",
        "自定义人设": ""
    }

    system_prompt = role_prompt_dict[role_choice]
    if role_choice == "自定义人设":
        system_prompt = st.text_area("自定义你的AI人设：", placeholder="例如：你是温柔的情感陪伴者...", height=120)

    st.divider()
    st.info("💡 切换人设后请清空对话，重新开始对话生效")

# ========== 初始化对话记忆 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []

# 每次切换人设，重置对话（把系统提示词放最前面）
if st.sidebar.button("🗑️ 清空对话并应用新人设", type="primary", use_container_width=True):
    st.session_state.messages = [{"role": "system", "content": system_prompt}]
    st.rerun()

# 没有系统提示词就初始化
if not st.session_state.messages:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# ========== 展示历史聊天 ==========
for msg in st.session_state.messages[1:]:  # 跳过系统提示词不展示
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 用户聊天输入 ==========
user_input = st.chat_input("和专属AI助手聊天吧...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    answer_container = st.empty()
    full_answer = ""

    with st.chat_message("assistant"):
        with st.spinner("AI正在思考..."):
            try:
                data = {
                    "model": MODEL_NAME,
                    "messages": st.session_state.messages,
                    "stream": True,
                    "max_tokens": 2048,
                    "temperature": 0.7
                }

                response = session.post(
                    BASE_URL,
                    json=data,
                    timeout=(10, 60)
                )
                response.raise_for_status()

                for line in response.iter_lines(decode_unicode=True):
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data: "):
                        line = line[6:]
                    if line == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0]["delta"]
                            if "content" in delta:
                                full_answer += delta["content"]
                                answer_container.markdown(full_answer)
                    except json.JSONDecodeError:
                        continue

                st.session_state.messages.append({"role": "assistant", "content": full_answer})
                st.success("✅ 回答完成！")

            except requests.exceptions.ConnectionError:
                st.error("❌ 网络连接失败，请关闭代理/VPN")
            except requests.exceptions.Timeout:
                st.error("❌ 请求超时，请稍后重试")
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    st.error("❌ API Key无效")
                elif response.status_code == 429:
                    st.error("❌ 请求太频繁，请稍后")
                else:
                    st.error(f"❌ 接口错误：{str(e)}")
            except Exception as e:
                st.error(f"❌ 程序出错：{str(e)}")

# 底部提示
st.divider()
st.caption("✨ 智谱GLM‑4.5‑Flash｜支持人设切换｜多轮记忆｜流式输出")
st.rerun()

# 底部提示
st.divider()
st.caption("💡 提示：使用智谱AI glm-4.5-flash 模型，支持多轮上下文记忆+流式实时输出")
