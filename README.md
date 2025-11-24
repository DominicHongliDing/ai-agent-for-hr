# ai-agent-for-hr

一个面向医学研究院校招的轻量级 AI Agent。通过 Streamlit 提供可视化界面，帮助 HR 初学者快速完成「CV 解析 → 匹配分析 → 个性化邀约邮件」的完整流程。

## 快速开始

### 0) 克隆代码

```bash
git clone https://github.com/<your-org>/ai-agent-for-hr.git
cd ai-agent-for-hr
```

### 1) 准备 Python 环境

- 建议使用 Python 3.10+。
- 新手可以开一个虚拟环境，防止污染全局依赖：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
```

### 2) 安装依赖

```bash
pip install -r requirements.txt
```

### 3) 启动前端（默认本地 8501 端口）

```bash
streamlit run app.py
```

### 4) 访问页面

浏览器打开 http://localhost:8501 ，即可看到 Streamlit 界面。

### 5) 在侧边栏配置模型

- Provider：`openai` 或 `anthropic`
- Model name：例如 `gpt-4o` 或 `claude-3-5-sonnet-20240620`
- API Key：对应平台的密钥

> 不填 API Key 时，简易解析会使用启发式规则（不调用大模型）。

### 6) API Key 配置指南（OpenAI / Anthropic）

**方式 A：在命令行设置环境变量（推荐）**

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# 然后启动 Streamlit
streamlit run app.py
```

**方式 B：在界面侧边栏直接输入**

1. 进入页面后，在侧边栏选择 Provider（OpenAI 或 Anthropic）。
2. 如果环境变量已设置，对应的 API Key 会自动填入；否则手动粘贴即可。
3. 使用 `gpt-4o-mini` / `claude-3-5-sonnet-20240620` 等模型名称进行解析、匹配和邮件生成。
4. 只有在需要 LLM 能力的步骤（开启 “Use LLM parsing”、生成 Matching/Outreach）才会调用 API，避免多余消耗。

> **新 SDK 提示（OpenAI >=1.0）**：如果你在自己的脚本里调用模型，请使用新的 `langchain_openai` 写法，例如：
>
> ```python
> from langchain_openai import ChatOpenAI
>
> llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
> ```
>
> App 里已采用上述标准方式，默认模型也设为 `gpt-4o-mini`，方便体验速度与成本的平衡。

## 界面说明

- **Resume Analysis**：上传 PDF 简历，或点击「加载示例简历」直接体验。可选择是否使用 LLM 解析（需 API Key）。解析结果以 JSON 和表格形式展示。
- **Matching Report**：选择已解析的候选人，输入目标研究方向（如 “Immunology”），生成 0-100 适配度评分、优势、差距与推荐项目。
- **Outreach Writer**：基于匹配分析，一键生成中/英文个性化邀约邮件。

## 使用 Tips

- PDF 解析异常时，可改用示例简历或先关闭 “Use LLM parsing”。
- 如果模型输出格式不合法，界面会自动回退到启发式结果，保证流程不中断。
- 推荐准备 2-3 句机构卖点（平台、启动经费、城市优势）放入 Outreach，以提升邮件吸引力。

祝你玩得开心，也欢迎在此基础上继续扩展功能。
