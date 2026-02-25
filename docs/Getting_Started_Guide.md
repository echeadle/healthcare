# How to Start a Claude Code Project (From Scratch)

## Prerequisites & Installation

1. **Subscribe to a Claude Pro plan** — You need a paid subscription to access Claude Code. Sign up at anthropic.com and set up your payment details.

2. **Install Claude Code globally** — Open your terminal and run:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

3. **Authenticate** — On first use, run `claude` and follow the login prompts (`/login`) to authenticate with your Anthropic account.

4. **Install an IDE (optional but recommended)** — Download VS Code, Cursor, or Windsurf. If using VS Code, install the "Claude Code" extension from the marketplace.

## Project Setup

5. **Create your project folder** — Pick a location and create a new directory:
   ```bash
   mkdir ~/Projects/my-project
   ```

6. **Initialize a git repository** — Claude Code relies heavily on git for long-term memory and context:
   ```bash
   cd ~/Projects/my-project
   git init
   ```

7. **Copy the starter template into your project** — The starter template includes pre-built commands, skills, and templates that automate the workflow described in this guide. Copy the template contents into your new project directory. The template has this structure:

   ```
   project-template/
   ├── .agents/
   │   └── plans/.gitkeep              # Where feature plans get saved
   ├── .claude/
   │   ├── CLAUDE-template.md          # Blank template for creating your CLAUDE.md
   │   ├── commands/
   │   │   ├── commit.md               # /commit — atomic git commits
   │   │   ├── create-prd.md           # /create-prd — generate a PRD from conversation
   │   │   ├── create-rules.md         # /create-rules — generate CLAUDE.md from codebase
   │   │   ├── execute.md              # /execute — run an implementation plan
   │   │   ├── plan-feature.md         # /plan-feature — create an implementation plan
   │   │   └── prime.md                # /prime — orient Claude at session start
   │   ├── rules/.gitkeep              # Modular rule files go here
   │   ├── settings.json               # Pre-configured tool permissions
   │   └── skills/
   │       └── agent-browser/SKILL.md  # Browser automation for E2E testing
   ├── .env.example                    # Placeholder for secrets (copy to .env)
   ├── .gitignore                      # Ignores .env, node_modules, build output, etc.
   ├── docs/
   │   └── Getting_Started_Guide.md    # Step-by-step guide (this document)
   ├── LICENSE                         # MIT license
   └── README.md                       # Project overview and quick start
   ```

   **Commands** (invoked with `/command-name` inside Claude Code):
   | Command | What It Does |
   |---------|-------------|
   | `/create-prd` | Generates a structured PRD from your brainstorming conversation |
   | `/create-rules` | Analyzes your codebase and generates a CLAUDE.md using the included template |
   | `/prime` | Primes Claude at the start of each session — reads docs, checks git log, builds a mental model |
   | `/plan-feature` | Creates a comprehensive implementation plan for a feature (the "Plan" in PIV) |
   | `/execute` | Executes an implementation plan step-by-step (the "Implement" in PIV) |
   | `/commit` | Creates an atomic git commit with a descriptive, tagged message |

8. **Launch Claude Code in the project folder** — Navigate to your folder and start Claude:
   ```bash
   cd ~/Projects/my-project
   claude
   ```

## Planning Phase (Before Writing Any Code)

> **Important:** Do NOT run `/init` yet. That command scans your existing codebase to generate a CLAUDE.md summary — but on an empty folder it has nothing to work with. Instead, plan your project first and create the CLAUDE.md manually afterward, informed by your planning decisions.

> **Which mode to use:** Stay in **regular mode** for this entire planning phase. Plan Mode is designed to research an existing codebase and produce implementation plans — but with an empty folder, there's nothing for it to analyze. Regular mode is fully conversational, which is exactly what you need for brainstorming and back-and-forth Q&A. Save Plan Mode for later, when you're implementing features and there's actual code to work with.
>
> | Phase | Mode | Why |
> |-------|------|-----|
> | Brainstorming & PRD creation | **Regular mode** | Conversational, no code to analyze yet |
> | Feature implementation planning (PIV loops) | **Plan Mode** | Researches codebase, produces structured plans |
> | Coding / executing a plan | **Regular mode** | Executing the approved plan |

9. **Brainstorm with Claude in regular mode** — Start a conversation. Describe your app idea in plain language. Use speech-to-text tools (like Whisper or built-in dictation) if you think faster than you type. Dump your ideas freely — Claude will help you structure them.

10. **Let Claude ask clarifying questions** — Encourage Claude to ask questions rather than make assumptions. Answer them to reduce misalignment before any code is written. This back-and-forth is where you nail down the real requirements.

11. **Create a Product Requirements Document (PRD)** — Once you've brainstormed enough, run the included command:
    ```
    /create-prd PRD.md
    ```
    This command extracts everything from your conversation and generates a structured PRD covering: executive summary, MVP scope, user stories, tech stack, implementation phases, and more. It saves to the filename you provide. Review it and refine as needed.

12. **Break the PRD into phases** — The `/create-prd` command automatically organizes work into implementation phases. Review them and adjust — each phase should be a manageable chunk that can be planned, implemented, and validated independently.

## Configuration & Rules (Building Your AI Layer)

13. **Create your CLAUDE.md using the template** — Now that you have a plan, run the included command:
    ```
    /create-rules
    ```
    This command analyzes your PRD and project setup, then generates a `CLAUDE.md` file using the included `.claude/CLAUDE-template.md` as a starting point. The CLAUDE.md is your "project brain" — it gets injected at the start of every conversation. Review the output and ensure it has:
    - Critical rules at the top (Claude has primacy bias — it remembers the beginning best)
    - Tech stack and architecture overview
    - Coding conventions and patterns
    - Bullet points for high information density
    - Keep it concise — avoid dumping entire API docs or style guides

    > **Note:** For existing codebases with lots of files, `/create-rules` is even more powerful — it analyzes your actual code to extract patterns and conventions. `/init` (the built-in Claude Code command) is an alternative but produces a more generic result.

14. **Create modular rules** — As your project grows, break the CLAUDE.md into smaller, focused rule files stored in `.claude/rules/` for modular organization (e.g., `code-style.md`, `testing.md`, `security.md`).

15. **Set up environment variables** — Create a `.env.example` file with placeholder values so Claude can run tests and implementations without getting blocked by missing env vars.

16. **Configure permission modes** — Choose your comfort level:
    - **Ask before edits** (default, safest)
    - **Edit automatically** (edits existing files freely, asks for new files)
    - **Plan mode** (research and plan before acting)
    - **Bypass permissions** (full autonomy — use with caution)

17. **Make your first commit** — Use the included commit command:
    ```
    /commit
    ```
    This runs `git status` and `git diff`, then creates an atomic commit with an appropriate tag (e.g., `docs:`, `feat:`, `fix:`) and descriptive message. This first commit establishes the baseline for your git history, which Claude uses as long-term memory.

## Development Workflow (PIV Loops)

18. **Start each session with `/prime`** — At the beginning of every new Claude Code session, run:
    ```
    /prime
    ```
    This command has Claude read your PRD, CLAUDE.md, README, check the git log, analyze the project structure, and output a summary of its understanding. Review the summary to confirm Claude is oriented correctly before giving it new work.

19. **Plan with `/plan-feature` (use Plan Mode)** — Switch to Plan Mode (`Shift+Tab` to cycle modes), then run:
    ```
    /plan-feature add user authentication
    ```
    This command performs deep codebase analysis, external research, pattern recognition, and produces a comprehensive implementation plan saved to `.agents/plans/`. The plan includes step-by-step tasks, validation commands, testing strategy, and acceptance criteria — all designed for one-pass implementation success.

20. **Implement with `/execute` (switch back to regular mode)** — Once you approve the plan, start a new conversation (to reset context), switch back to regular mode, and run:
    ```
    /execute .agents/plans/add-user-authentication.md
    ```
    This command reads the plan and executes every task in order, verifying as it goes, running validation commands, and producing a completion report.

21. **Validate** — The `/execute` command runs validations as part of its process, but also do your own review using the validation pyramid:
    - Type checking / linting
    - Unit tests
    - Integration tests
    - End-to-end tests (the `agent-browser` skill is available for browser-based E2E testing)
    - Human review (trust but verify)

22. **Commit with `/commit`** — After each successful phase:
    ```
    /commit
    ```
    Creates an atomic commit with a tagged, descriptive message. This builds up the git log that `/prime` reads at the start of each session, giving Claude long-term memory of the project's evolution.

23. **Repeat the PIV loop** — Move to the next phase and repeat: `/plan-feature` → `/execute` → validate → `/commit`.

## Ongoing Best Practices

24. **Use sub-agents for specialized tasks** — Spin up research agents, reviewer agents, and QA agents to keep the main context focused and unbiased.

25. **Evolve your AI layer over time** — When you find a bug or inconsistency, don't just fix it — update your rules, add tests, and refine your CLAUDE.md to prevent it from recurring (system evolution mindset).

26. **Manage context carefully** — Use progressive disclosure: only give Claude the context it needs for the current task. Avoid information overload. Start new conversations when context gets stale. The `/prime` command helps re-establish context cleanly at the start of each session.

27. **Create reusable commands and skills** — The starter template gives you six commands out of the box, but you should add your own as you find repeated workflows. Commands are user-initiated (you type `/command-name`), while skills are AI behaviors that Claude can invoke automatically.

28. **Set up automated testing** — Establish a testing framework early so regression tests grow alongside your features. The included `agent-browser` skill provides browser automation for E2E testing.

29. **Deploy when ready** — Building is local; deploying makes it accessible. Use services like Vercel, Netlify, or GitHub Actions for deployment when your MVP is validated.

---

## Quick Reference: Starter Template Commands

| Command | When to Use | What It Does |
|---------|-------------|-------------|
| `/create-prd PRD.md` | After brainstorming (step 11) | Generates a structured PRD from your conversation |
| `/create-rules` | After PRD is done (step 13) | Analyzes project and generates CLAUDE.md |
| `/prime` | Start of every session (step 18) | Orients Claude on the codebase and recent changes |
| `/plan-feature <name>` | Before implementing a feature (step 19) | Creates a detailed implementation plan in `.agents/plans/` |
| `/execute <plan-path>` | After approving a plan (step 20) | Executes the plan step-by-step with validation |
| `/commit` | After completing work (step 22) | Creates a tagged, descriptive git commit |

---

*This guide combines the structured "Cole workflow" (PIV loops, PRD-first, four golden rules) and the broader "Full course" material (installation, IDE setup, CLAUDE.md best practices, permission modes, agents/skills). The key takeaway: **plan before you code, keep context clean, and evolve your system as you go.***
