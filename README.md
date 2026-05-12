# ExpenseManager

Lite Flask App for Expense Tracking and Management

Qwen Response Hacks:

To turn **Qwen 2.5 Coder 7b** from a "clumsy" model that overwrites files into a precision instrument, you need to tighten the constraints in your `config.json` (or `config.yaml`) and change how you interact with the **Continue** interface.

---

### 1. Updating Configuration

The `config.yaml` (or `.json`) is where you define the model's technical boundaries. According to the [Continue reference](https://docs.continue.dev/reference), you should focus on `requestOptions` and `systemMessage`.

**Recommended Config Update:**

```yaml
models:
  - name: Qwen 2.5 Coder 7b
    provider: ollama
    model: qwen2.5-coder:7b
    systemMessage: |
      You are a specialized code refactoring assistant. 
      Your goal is to provide surgical, minimal code updates.
      Always prioritize existing project patterns (e.g., Singleton Database).
    requestOptions:
      temperature: 0.1 # Lower temperature = less "creativity" and more precision
      contextLength: 8192 # Ensure enough space for Flask + Jinja files
```

---

### 2. Fine-Tuning via Rules and Agents

Continue uses `.prompt` files and the `baseAgentSystemMessage` to set behavioral guardrails. This is the "brain" of the agent.

- **Custom Rules:** Create a file named `.continuerc.json` in your root or update the global config to include **Rules**.
- **The "Surgical" Rule:** Add this to your `baseAgentSystemMessage`:
  > "When editing, only output the changed lines. Do not rewrite the entire file unless explicitly asked. Use comments like `// ... existing code` to indicate skipped sections."

---

### 3. Solving the "Bad Response" Issues

#### Issue: Fix of one file breaks another.

- **The Fix:** Use **Context Providers**. Before asking for a fix, type `@` in the chat and select `@Files` or `@Codebase`. Specifically, highlight the related file (e.g., `database.py`) while editing `index.html`. This forces the model to check for dependency conflicts.

#### Issue: Writing the entire file instead of fixing code.

- **The Fix:** **Stop using the Chat Sidebar for edits.** Use **`Ctrl + I`** (Inline Edit) instead.
- The sidebar is for "talking."
- Inline Edit is for "doing."
- When you use `Ctrl + I`, Continue sends a "diff" request to the model, which naturally encourages it to only change the lines you've highlighted.

#### Issue: Keeping current code and files intact.

- **The Fix:** Use the **"Diff" View**. When the model suggests a change, Continue shows a side-by-side comparison. **Review it line-by-line.** If the model tries to delete your existing code, use the "Reject" button on those specific lines or refine your prompt: _"Add the Edit button to the table row without changing any existing column logic."_

---

### 4. Resetting Hallucinations Quickly

When the model starts "looping" or giving nonsense (hallucinating), you need to clear its "Short-Term Memory."

- **The "New Session" Shortcut:** Press `Ctrl + Shift + L` (or `Cmd + Shift + L`) to start a fresh chat. This clears all previous context that might be confusing the model.
- **Kill the Ollama Process:** If the model is stuck in a loop, it might be an Ollama hang.

1. Open your terminal.
2. Run `ollama stop qwen2.5-coder:7b`.
3. Ask a new question in Continue; Ollama will restart automatically with a clean slate.

- **The "Abort" Command:** If the model starts writing a massive file you didn't ask for, immediately hit **`Esc`** or click the **Stop** icon in the Continue sidebar to kill the generation.

---

### Summary Checklist for Better Code

| Issue                | Solution                                |
| -------------------- | --------------------------------------- |
| **Hallucination**    | `Ctrl + Shift + L` (New Session)        |
| **Overwriting File** | Use `Ctrl + I` instead of Sidebar Chat  |
| **Breaking Logic**   | `@` reference related files for context |
| **Generic Output**   | Set `temperature: 0.1` in config        |

**Next Step:** Try adding the `Edit` button again using **`Ctrl + I`** and specifically mention: _"Modify only the `<td>` actions, do not touch the `{{ expense.amount }}` logic."_

### 1. Updated `systemMessage` (Model Personality)

This goes inside your `models` block for Qwen in `config.json`. It defines the model's focus on UI/UX and Jinja2.

```json
"systemMessage": "You are a Frontend Engineer specializing in Flask templates. Your domain is strictly HTML, CSS, and JavaScript within the context of Jinja2. Always use existing project CSS classes. When modifying files, preserve all backend logic ({{ ... }} tags) exactly as they are. If a change requires a new Flask route, simply name the route and provide the HTML; do not attempt to write the Python backend code unless asked."

```

---

### 2. `baseAgentSystemMessage` (Refactoring Rules)

These rules are the "guardrails" that prevent the model from rewriting your entire file.

```text
"baseAgentSystemMessage": "Follow these rules for every request:
1. SURGICAL UPDATES: Only output the specific lines of code that need to be added or changed. Use '// ... existing code' to represent untouched blocks.
2. FRONTEND SCOPE: Prioritize CSS styling and HTML structure. Ensure all forms and buttons follow the existing Bootstrap/UI theme.
3. JINJA PRESERVATION: Never remove or alter existing Jinja loops ({% for ... %}) or variables unless the feature specifically requires it.
4. SINGLE FEATURE FOCUS: If the user asks for 'Edit Expense', do not suggest changes for 'Delete' or 'Add' in the same response.
5. NO FULL REWRITES: Never output the entire file content. Only provide the diff or the specific container being modified."

```

---

### 3. Strategy: Limiting Scope per Session

Yes, you can and **should** limit the scope. Here is how to manage a session focused solely on the "Edit Form" feature:

#### The "Single-Feature" Workflow:

1. **Context Loading:** Type `@` and select your `index.html`.
2. **Explicit Instruction:** Start your prompt by defining the boundary:

   > "Focusing **only** on the 'Edit Expense' feature: Add a hidden modal form to `index.html` that will capture the expense ID, amount, and category. Use the existing CSS classes."

3. **The "Surgical" Trigger:** If the model starts writing the whole file, stop it immediately and refine:
   > "Stop. Only show me the code for the `<div class='modal'>` and the JS function to toggle it."

---

### 4. Better Responses for Frontend Tasks

To prevent the "breaking other files" issue, follow this interaction pattern:

| Goal               | Prompt Technique                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------ |
| **Styling**        | "How can I style the Edit button to match the 'Delete' button in my current `static/style.css`?"       |
| **Form Logic**     | "Add a POST form for editing. Use `url_for('edit_expense')`. Only provide the `<form>` block."         |
| **JS Interaction** | "Write a script to populate the form fields when the edit button is clicked. Do not modify the table." |

### How to Reset Preferences Quickly

If the model begins to hallucinate or tries to write Python code in your HTML file:

1. **Clear Context:** `Ctrl + Shift + L` to wipe the session memory.
2. **Hard Reset:** If you are using the **Continue** extension, click the **"History"** icon and delete the current thread.
3. **The "Rule" Reminder:** Type: _"Stick to the frontend-only rules. Do not rewrite the file. Only the edit form modal."_

**Next Logical Step:**
Try the **`Ctrl + I`** shortcut on your table row and use this prompt: _"Add a button to this row that opens an Edit Modal. Provide only the `<td>` and the modal HTML."_ Does it give you a surgical update now?
