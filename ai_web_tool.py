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
st.set_page_config(page_title="智谱AI问答工具", page_icon="🤖", layout="wide")
st.title("🤖 我的专属AI问答小工具")
st.divider()

# 获取用户输入
user_input = st.text_input(
    "请输入你想问的问题：",
    placeholder="比如：帮我写一条朋友圈文案、解释一下Python的装饰器",
    max_chars=2000
)

# 点击按钮触发AI调用
if st.button("生成回答", type="primary", use_container_width=True):
    if not user_input.strip():
        st.warning("⚠️ 请先输入你的问题哦！")
    else:
        # 流式输出容器（实时显示AI回答）
        answer_container = st.empty()
        full_answer = ""
        
        with st.spinner("AI正在思考中..."):
            try:
                # 构造请求体（兼容OpenAI格式）
                data = {
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": user_input}],
                    "stream": True,  # 开启流式输出，解决卡顿延迟
                    "max_tokens": 2048,
                    "temperature": 0.7
                }

                # 发送请求
                response = session.post(
                    BASE_URL,
                    json=data,
                    timeout=(10, 60)  # 连接超时10秒，读取超时60秒
                )
                response.raise_for_status()  # 提前捕获HTTP错误（401/403/500等）

                # 逐行解析流式响应，实时显示
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

                # 生成完成提示
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

# 底部提示
st.divider()
st.caption("💡 提示：使用智谱AI glm-4.5-flash 模型，永久免费无调用门槛，支持流式输出不卡顿")