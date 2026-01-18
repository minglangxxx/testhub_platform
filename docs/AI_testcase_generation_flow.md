**AI Testcase Generation 流程说明**

本文档走读并梳理项目中 AI 自动生成测试用例的完整流程，覆盖：
- **前端配置与触发**
- **后端任务与模型配置**
- **后端调用 AI（兼容 OpenAI 格式）**
- **后端解析 AI 响应与入库流程**
- **替换为本地 Qwen 的接入要点**
- **用 RAG+知识库 提升用例质量的建议**

**主要代码位置**
- **前端（UI/触发）**: [frontend/src/views/requirement-analysis/RequirementAnalysisView.vue](frontend/src/views/requirement-analysis/RequirementAnalysisView.vue)
- **前端（AI 模型配置）**: [frontend/src/views/configuration/AIIntelligentModeConfig.vue](frontend/src/views/configuration/AIIntelligentModeConfig.vue)
- **后端模型/配置定义**: [apps/requirement_analysis/ai_models.py](apps/requirement_analysis/ai_models.py)
- **后端服务逻辑（文档提取 / AI 调用 / 生成/校验）**: [apps/requirement_analysis/services.py](apps/requirement_analysis/services.py)
- **智能分析器（更复杂的 LLM 驱动分析/抽取逻辑）**: [apps/requirement_analysis/advanced_analyzer.py](apps/requirement_analysis/advanced_analyzer.py)
- **后端路由 / 视图（REST endpoints）**: [apps/requirement_analysis/urls.py](apps/requirement_analysis/urls.py) 和 [apps/requirement_analysis/views.py](apps/requirement_analysis/views.py)

**整体流程概览（简要）**
1. 用户在 `RequirementAnalysisView.vue` 页面上传文档或手工输入需求文本，点击“生成测试用例”。
2. 前端调用后端接口创建一个 TestCase 生成任务：`POST /requirement-analysis/api/testcase-generation/generate/`（见前端代码发起请求）。
3. 后端创建 `TestCaseGenerationTask` 记录（模型配置、prompt 配置、任务 id 等），把状态置为 `pending`，随后异步执行生成流程。
4. 后端（服务层）先进行文档提取 / 预处理（见 `DocumentProcessor.extract_text`），如需要调用 `AdvancedTestRequirementAnalyzer` 做深度分析。
5. 后端根据任务配置，准备 prompt（`PromptConfig`）和模型配置（`AIModelConfig`），组织 `messages`（system / user）并调用 `AIModelService.call_openai_compatible_api`。
6. AI 返回文本（一般在响应的 `choices[0].message.content`），后端解析该文本为结构化的测试用例（或直接保存富文本），创建 `GeneratedTestCase` 记录并更新任务状态（`generating` → `reviewing` → `completed`）。
7. 前端轮询任务进度（`GET /requirement-analysis/api/testcase-generation/{task_id}/progress/`），在任务完成后显示生成结果并支持下载/保存到测试用例库。

**详细流程与关键点**

**1) 前端触发点与上传逻辑**
- 页面: [frontend/src/views/requirement-analysis/RequirementAnalysisView.vue](frontend/src/views/requirement-analysis/RequirementAnalysisView.vue)
- 触发流程的关键方法:
  - `generateFromDocument()`：上传文件到 `POST /requirement-analysis/api/documents/`，再调用 `GET /documents/{id}/extract_text/` 提取文本。
  - `generateFromManualInput()`：直接把用户输入的 `title` 与 `description` 拼接成 `requirement_text`。
  - 两种入口最终都调用 `startGeneration(title, requirementText, projectId)`，它会 `POST /requirement-analysis/api/testcase-generation/generate/`，并开始轮询任务状态。

**2) 后端入口与任务创建**
- 后端视图（action）负责接收前端请求并创建任务记录（模型/prompt 选项可由前端传入或使用默认配置）。核心位置：
  - [apps/requirement_analysis/views.py](apps/requirement_analysis/views.py) 中与 `TestCaseGenerationTask` 相关的 `generate` action（前端请求路径 `/testcase-generation/generate/`）。
  - 模型与 prompt 的表模型定义在 [apps/requirement_analysis/ai_models.py](apps/requirement_analysis/ai_models.py) 的 `AIModelConfig` 与 `PromptConfig`。

**3) 后端执行流程（services 层）**
- 文档提取: `DocumentProcessor.extract_text(document)`（在 [apps/requirement_analysis/services.py](apps/requirement_analysis/services.py) 与 `views.py` 中被调用）。
- 分析器: `AdvancedTestRequirementAnalyzer`（[apps/requirement_analysis/advanced_analyzer.py](apps/requirement_analysis/advanced_analyzer.py)）用于将原始文本转成结构化需求点、测试场景、测试类型等（可作为 prompt 的上下文）。
- 生成步骤（伪流程）:
  1. 创建或选择 `writer_model_config` / `reviewer_model_config`（`AIModelConfig`）和 `writer_prompt_config` / `reviewer_prompt_config`（`PromptConfig`）。
  2. 组装 `messages`：
     - system: 来自 `writer_prompt_config.content`
     - user: 包含 `requirement_text`（以及可选的结构化上下文）
  3. 调用 `AIModelService.call_openai_compatible_api(config, messages)`（[apps/requirement_analysis/ai_models.py](apps/requirement_analysis/ai_models.py)），等待返回。
  4. 将返回文本（通常在 `response['choices'][0]['message']['content']`）解析为测试用例列表或 HTML 富文本，创建 `GeneratedTestCase` 实例（见 `services.py` 中 `generate_test_cases_for_requirements` 的实现）。
  5. 如果启用了 reviewer，则把生成的用例传给 reviewer 模型（相同方式）得到 review 反馈，合并并更新 `TestCaseGenerationTask` 的 `final_test_cases`。

**4) 后端调用 AI 的实现细节**
- 统一调用函数：`AIModelService.call_openai_compatible_api(config, messages)`。
  - 它使用 `httpx.AsyncClient` 发起 `POST` 到 `url`，默认会将 `config.base_url` 做后缀补全：
    - 若 `base_url` 不以 `/chat/completions` 结尾，代码会尝试把 `/v1/chat/completions` 或 `/chat/completions` 拼接上去（见实现）。
  - 请求 body 示例（JSON）:

```json
{
  "model": "<config.model_name>",
  "messages": [ {"role": "system", "content": "..."}, {"role": "user", "content": "..."} ],
  "max_tokens": 4096,
  "temperature": 0.7,
  "top_p": 0.9,
  "stream": false
}
```

- 响应解析（通用）：
  - 成功：`response.json()`，内容按 OpenAI ChatCompletion 格式：`choices[0].message.content`。后端现有代码直接取该字段作为生成文本。
  - 错误：`httpx` 抛出错误或返回非 200，`AIModelService` 会记录并抛出异常，任务会标为 `failed` 并写入 `error_message`。

**5) 解析 AI 响应并入库**
- 后端有两类解析策略：
  - 简单模式（当前大量使用）：直接把返回的富文本作为 `generated_test_cases` 或 `final_test_cases` 存为 HTML/文本；同时还会视情况生成若干 `GeneratedTestCase` 记录（结构化字段）。具体实现可见 `services.py` 中的 `generate_test_cases_for_requirements`。
  - 高级模式（可扩展）：在 `advanced_analyzer` 或自定义解析器中，把 LLM 返回的结构化 JSON（建议让 LLM 输出 JSON）解析为多个 `GeneratedTestCase` 字段并保存。

**6) 前端如何展示与下载**
- 前端轮询接口：`GET /requirement-analysis/api/testcase-generation/{task_id}/progress/`，返回任务当前 `status` 与 `progress`、最终包含 `generated_test_cases` / `final_test_cases` / `review_feedback`。
- 下载逻辑在 `RequirementAnalysisView.vue` 中把 `final_test_cases` 或解析后的表格转为 xlsx 并触发浏览器下载。

**如何把 AI 替换为本地 Qwen（步骤）**
（你已在本地部署 Qwen，下面给出接入要点）

- 1) 在后台新增或编辑 `AIModelConfig`：
  - `model_type` 选 `qwen` 或 `other`（`ai_models.AIModelConfig.MODEL_CHOICES` 已包含 `qwen`），
  - `base_url` 填写你的本地 Qwen 的 HTTP API 根地址，推荐写到能被库直接使用的形式，例如：
    - 如果 Qwen 提供 OpenAI 兼容的 `v1/chat/completions`：`http://127.0.0.1:8000/v1` 或 `http://127.0.0.1:8000`（系统会自动拼接 `/v1/chat/completions`）。
    - 或者直接写完整的 `http://127.0.0.1:8000/v1/chat/completions`。
  - `api_key`：如果你的 Qwen 实例需要 token，则填写；否则可以写空或一个占位。

- 2) 测试连接：前端有“测试连接”按钮（见 [frontend/src/views/configuration/AIIntelligentModeConfig.vue](frontend/src/views/configuration/AIIntelligentModeConfig.vue)），会触发后端 `test_connection` action，验证是否能访问 Qwen 接口。

- 3) 注意兼容性：
  - 本项目的 `AIModelService.call_openai_compatible_api` 期望 OpenAI 风格的 `chat/completions` JSON/返回。如果 Qwen 的接口兼容 OpenAI 格式（多数 qwen 接口可配置为兼容），则无需改动；否则在 `ai_models.py` 中添加或修改 `call_qwen_api` 的实现，做响应映射（把 Qwen 的返回映射为 `choices[0].message.content` 格式）。
  - 若 Qwen 的速率或并发不同，考虑在 `httpx.AsyncClient` 中调整 `timeout` 或重试策略。

**RAG（检索增强生成）集成建议（高阶）**

目标：把知识库 / 需求文档作为检索上下文，检索出最相关的片段并在 prompt 中拼接，从而产生更准确、基于证据的测试用例。

- 关键点：
  - 建立文本存储（向量数据库），常见选型：FAISS / Milvus / Weaviate / Pinecone / Chroma。
  - 选用 Embedding 模型（内网/云端均可），把需求文档、历史测试用例、手册等索引为向量。
  - 在生成流程中（`services.generate_test_cases` 前），先对 `requirement_text` 做检索，取 top-k 文档片段，合并成 `context`。
  - 将 `context` 放入 `messages` 的 system 或 user 段，明确告诉 LLM："以下是相关文档片段（按相关性排序）——请在生成测试用例时引用并标注来源"。

- 代码级接入点：
  - 在 [apps/requirement_analysis/services.py](apps/requirement_analysis/services.py) 中生成 prompt 前调用检索模块：例如 `context = retriever.get_topk(requirement_text, k=5)`，然后把 `user_message = f"相关上下文:\n{context}\n\n请根据以下需求生成测试用例：\n{requirement_text}"`。
  - 若使用 `langchain`，可用 `RetrievalQA` / `RAG chain` 或自定义 chain，把检索与 LLM 调用串联。

**示例：把本地检索结果注入 prompt（伪代码）**

```python
# retriever 为向量索引客户端
context_chunks = retriever.similarity_search(requirement_text, k=5)
context_text = "\n---\n".join([c['text'] for c in context_chunks])

messages = [
    {"role": "system", "content": writer_prompt},
    {"role": "user", "content": f"相关文档:\n{context_text}\n\n需求:\n{requirement_text}"}
]
response = await AIModelService.call_openai_compatible_api(model_config, messages)
```

**常见问题与排查建议**
- 如果前端一直轮询但任务不动：检查后端任务创建逻辑（数据库的 `TestCaseGenerationTask` 是否创建），以及 Celery/异步 loop 是否在运行（项目用 `async` 直接执行也会 block）。
- 如果 AI 返回空或格式不正确：先在管理界面用“测试连接”功能调试 `AIModelConfig` 的 `base_url` 与 `api_key`，确认后端 `AIModelService.call_openai_compatible_api` 能拿到 `response.json()` 并包含 `choices`。
- Token/截断问题：若上下文太长，OpenAI 类模型会因 `max_tokens` 或 prompt 长度截断，建议减少上下文或使用 RAG 将长文拆分并只注入 top-k 片段。

**流程图（ASCII / mermaid）**

Mermaid （若渲染器支持）：

```mermaid
flowchart TD
  A[前端: 用户上传文档或手工输入] --> B[创建任务: POST /testcase-generation/generate/]
  B --> C[后端: 创建 TestCaseGenerationTask]
  C --> D[文档提取 & 预处理]
  D --> E{是否使用检索(RAG)?}
  E -->|Yes| F[检索 top-k 文档片段]
  F --> G[组合 prompt + context]
  E -->|No| G
  G --> H[调用模型: AIModelService.call_openai_compatible_api]
  H --> I[解析 LLM 响应 -> 结构化用例]
  I --> J[保存 GeneratedTestCase 和任务状态更新]
  J --> K[前端轮询显示结果]
```

ASCII 图（终端查看友好）：

```
User -> Frontend -> POST /generate
                 Backend: create Task -> extract_text -> (RAG?) -> call LLM -> parse -> save cases
Frontend polls /progress -> display results
```

**建议与下一步（给你用于替换/优化的实际操作清单）**
1. 在管理控制台或前端 `AIIntelligentModeConfig` 添加/编辑 `AIModelConfig`，把 `base_url` 指向你的本地 Qwen 实例，填 API key（如果需要）。
2. 先用“测试连接”按钮验证连通性。
3. 如果返回格式不兼容，修改 `AIModelService.call_qwen_api`（在 `apps/requirement_analysis/ai_models.py` 添加转换逻辑），把 Qwen 的响应映射到 `choices[0].message.content`。
4. 要做 RAG：搭建向量数据库并实现一个简单的 `retriever` 模块（可放在 `apps/requirement_analysis/retriever.py`），在 `services.generate_test_cases` 中把检索结果注入 prompt。

**文档位置**
- 本文件已保存为 `docs/AI_testcase_generation_flow.md`（项目根目录下）。

-- 结束 --
