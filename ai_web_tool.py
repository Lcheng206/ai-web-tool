import streamlit as st
import requests
import json

# -------------------------- 核心配置（你的智谱信息，不用改） --------------------------
API_KEY = "e5f5f77520db4c1fb1298ff8006ce6f5.ZZjfpgRXAqbqBOyz"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL_NAME = "glm-4.5-flash"  # 官方最快免费模型，延迟最低

# 全局Session复用TCP连接（减少每次请求的握手延迟）
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept-Encoding": "gzip, deflate"
})

# -------------------------- Streamlit 页面配置 --------------------------
st.set_page_config(page_title="智谱多轮对话机器人", page_icon="🤖", layout="wide")
st.title("🤖 我的专属连续对话AI机器人")
st.divider()

# ========== 新增：初始化对话记忆 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []

# ========== 新增：展示历史所有聊天记录 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 聊天式输入框（替换原单行输入，更自然） ==========
user_input = st.chat_input("请输入问题，和AI连续聊天，AI会记住上下文...")

# 触发AI对话
if user_input:
    # 1. 保存用户消息到记忆并展示
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. AI流式回复
    answer_container = st.empty()
    full_answer = ""

    with st.chat_message("assistant"):
        with st.spinner("AI正在思考中..."):
            try:
                # 把【全部历史对话】传给智谱，实现记忆
                data = {
                    "model": MODEL_NAME,
                    "messages": st.session_state.messages,
                    "stream": True,  # 保持流式输出
                    "max_tokens": 2048,
                    "temperature": 0.7
                }

                response = session.post(
                    BASE_URL,
                    json=data,
                    timeout=(10, 60)
                )
                response.raise_for_status()

                # 逐行解析流式响应
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

                # 3. 保存AI回答到记忆
                st.session_state.messages.append({"role": "assistant", "content": full_answer})
                st.success("✅ 回答生成完成！")

            except requests.exceptions.ConnectionError:
                st.error("❌ 网络连接失败，请检查网络或关闭代理/VPN（智谱是国内节点，开代理会绕路）")
            except requests.exceptions.Timeout:
                st.error("❌ 请求超时，请稍后重试或缩短问题长度")
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    st.error("❌ API Key无效，请检查你的智谱API Key是否正确")
                elif response.status_code == 429:
                    st.error("❌ 请求过于频繁，请稍等一分钟再试")
                else:
                    st.error(f"❌ 接口错误：{str(e)}，状态码：{response.status_code}")
            except Exception as e:
                st.error(f"❌ 程序运行出错：{str(e)}")

# ========== 新增：清空对话按钮 ==========
if st.button("🗑️ 清空对话历史", type="secondary", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

# 底部提示
st.divider()
st.caption("💡 提示：使用智谱AI glm-4.5-flash 模型，支持多轮上下文记忆+流式实时输出")
