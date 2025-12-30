# TARS V2 Agent System - Complete Guide

## 🎯 How the System Decides Which Agent to Use

### The Decision Maker: Gemini AI

**The system doesn't explicitly "decide" - Gemini AI does!** Here's how:

1. **Tool Definitions** - Each agent has a tool definition with:
   - `name`: Unique identifier (e.g., "generate_cad", "run_web_agent")
   - `description`: What the tool does (Gemini reads this!)
   - `parameters`: What inputs it needs

2. **Gemini's Function Calling** - When you say something like:
   - "Create a cube" → Gemini sees `generate_cad` tool matches
   - "Go to Amazon" → Gemini sees `run_web_agent` tool matches
   - "Turn on the lights" → Gemini sees `control_light` tool matches

3. **Natural Language Understanding** - Gemini analyzes your request and matches it to the best tool based on:
   - Tool descriptions
   - Parameter requirements
   - Context of conversation

### Example Tool Definitions

```python
# From TARS.py
generate_cad = {
    "name": "generate_cad",
    "description": "Generates a 3D CAD model based on a prompt.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {"type": "STRING", "description": "The description of the object to generate."}
        },
        "required": ["prompt"]
    }
}

run_web_agent = {
    "name": "run_web_agent",
    "description": "Opens a web browser and performs a task according to the prompt.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {"type": "STRING", "description": "The detailed instructions for the web browser agent."}
        },
        "required": ["prompt"]
    }
}
```

**Key Point:** The `description` field is what Gemini reads to decide which tool to use!

---

## 📊 Complete User Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INPUT                                               │
│    "Create a hex bolt" or "Go to Amazon"                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. FRONTEND (React)                                         │
│    - Captures voice/text input                              │
│    - Sends via Socket.IO 'user_input' event                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SERVER (server.py)                                        │
│    - Receives Socket.IO event                               │
│    - Forwards to TARS.py AudioLoop.session                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. TARS (TARS.py)                                             │
│    - Sends user input to Gemini Live API                    │
│    - Gemini processes with all available tools              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. GEMINI AI DECISION                                       │
│    - Analyzes user request                                  │
│    - Matches to tool based on description                   │
│    - Returns tool_call with name + arguments                │
│    Example: {name: "generate_cad", args: {prompt: "..."}}  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. PERMISSION CHECK (TARS.py:848)                            │
│    - Checks settings.json tool_permissions                  │
│    - If True → Request user confirmation                    │
│    - If False → Auto-execute                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. TOOL HANDLER (TARS.py:872-1202)                          │
│    - Routes to specific handler based on tool name          │
│    - Calls appropriate agent method                          │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐        ┌───────────────┐
│ CAD Agent     │        │ Web Agent     │
│ generate()    │        │ run_task()    │
└───────┬───────┘        └───────┬───────┘
        │                        │
        ▼                        ▼
┌───────────────┐        ┌───────────────┐
│ Returns STL   │        │ Returns Result │
│ file          │        │ text           │
└───────┬───────┘        └───────┬───────┘
        │                        │
        └────────────┬───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. RESULT HANDLING                                          │
│    - Agent returns result                                   │
│    - Result sent back to Gemini via FunctionResponse        │
│    - Gemini generates natural language response             │
│    - Response streamed to frontend via Socket.IO            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 How Agents Work (General Pattern)

All agents follow a similar pattern:

### 1. **Agent Class Structure**

```python
class Agent:
    def __init__(self):
        # Initialize resources (API clients, connections, etc.)
        pass
    
    async def main_method(self, prompt, **kwargs):
        # Main entry point
        # 1. Process input
        # 2. Execute task
        # 3. Return result
        pass
```

### 2. **Integration Points**

**In `TARS.py`:**
- Agent initialized in `AudioLoop.__init__()` (line ~256-259)
- Tool handler calls agent method (line ~872-1202)
- Result returned to Gemini

**Example:**
```python
# Initialization
self.cad_agent = CTARSgent(on_thought=handle_cad_thought, on_status=handle_cad_status)
self.web_agent = WebAgent()

# Tool handler
elif fc.name == "generate_cad":
    asyncio.create_task(self.handle_cad_request(prompt))

# Handler method
async def handle_cad_request(self, prompt):
    cad_data = await self.cad_agent.generate_prototype(prompt, output_dir=...)
    # Send result to frontend
    self.on_cad_data(cad_data)
```

### 3. **Common Features**

- **Async/Await**: All agent methods are async
- **Error Handling**: Try/catch with meaningful error messages
- **Callbacks**: Agents can emit status updates via callbacks
- **Project Context**: Agents work within current project directory

---

## 🌐 How the Web Agent Works

### Architecture

The Web Agent uses **Gemini 2.5 Computer Use** model, which can:
- See the browser (via screenshots)
- Control the browser (via function calls)
- Make decisions autonomously

### Step-by-Step Process

```
1. User: "Go to Amazon and find a USB-C cable under $10"
   ↓
2. Gemini calls run_web_agent tool
   ↓
3. WebAgent.run_task() starts:
   ├─ Launches Playwright browser (headless)
   ├─ Takes initial screenshot
   ├─ Sends screenshot + prompt to Gemini Computer Use model
   ↓
4. Gemini Computer Use Model:
   ├─ Analyzes screenshot (sees Google homepage)
   ├─ Decides: "I need to navigate to Amazon"
   ├─ Calls function: navigate(url="https://amazon.com")
   ↓
5. WebAgent.execute_function_calls():
   ├─ Executes navigate() via Playwright
   ├─ Takes new screenshot
   ├─ Sends screenshot + result back to Gemini
   ↓
6. Gemini sees Amazon homepage:
   ├─ Decides: "I need to search for USB-C cable"
   ├─ Calls function: type_text_at(x, y, "USB-C cable")
   ├─ Calls function: click_at(search_button_x, search_button_y)
   ↓
7. Repeat steps 5-6 until task complete:
   ├─ Scroll, click, type, navigate
   ├─ Up to 20 turns (MAX_TURNS)
   ↓
8. Gemini determines task complete:
   ├─ Returns final summary text
   ├─ WebAgent returns result to main system
```

### Key Components

**1. Browser Control (Playwright)**
```python
# From web_agent.py
self.browser = await p.chromium.launch(headless=True)
self.page = await self.context.new_page()
await self.page.goto("https://www.google.com")
```

**2. Function Execution**
```python
# Gemini calls functions like:
- navigate(url)
- click_at(x, y)
- type_text_at(x, y, text)
- scroll_document(direction)
- drag_and_drop(x, y, dest_x, dest_y)

# WebAgent executes them via Playwright:
await self.page.mouse.click(x, y)
await self.page.keyboard.type(text)
```

**3. Visual Feedback Loop**
```python
# Each turn:
1. Take screenshot (PNG)
2. Send to Gemini with chat history
3. Gemini analyzes image + decides action
4. Execute action
5. Take new screenshot
6. Repeat
```

### Why It Works

- **Vision**: Gemini can "see" the page via screenshots
- **Autonomy**: Makes its own decisions about what to click/type
- **Context**: Maintains chat history across turns
- **Safety**: Has built-in safety checks (can request confirmation)

---

## 🧊 How the CAD Agent Generates 3D Models

### The Magic: Code Generation + Local Execution

The CAD Agent doesn't directly create 3D models. Instead, it:
1. **Asks Gemini to write Python code** (using build123d library)
2. **Executes that code locally** on your machine
3. **Generates an STL file** from the executed code

### Detailed Process

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: User Request                                        │
│ "Create a hex bolt"                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Gemini Calls generate_cad Tool                      │
│ Tool handler → cad_agent.generate_prototype("hex bolt")     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Ask Gemini 3 Pro for Code                            │
│ Prompt: "Write a build123d script to create a hex bolt"    │
│ Model: gemini-3-pro-preview                                  │
│ System Instruction: Detailed build123d guidelines           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Gemini Generates Python Code                        │
│                                                              │
│ ```python                                                    │
│ from build123d import *                                     │
│                                                              │
│ with BuildPart() as bolt:                                   │
│     # Hex head                                              │
│     with BuildSketch():                                     │
│         RegularPolygon(6, 10)  # 6 sides, 10mm radius      │
│     extrude(amount=5)                                        │
│                                                              │
│     # Threaded shaft                                        │
│     with Locations((0, 0, 5)):                             │
│         Cylinder(radius=3, height=20)                       │
│                                                              │
│ result_part = bolt.part                                     │
│ export_stl(result_part, 'output.stl')                       │
│ ```                                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Extract & Save Code                                 │
│ - Extract code from ```python block                         │
│ - Save to current_design.py                                  │
│ - Inject output path (replace 'output.stl' with full path)   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Execute Code Locally                                │
│ subprocess.run([python, current_design.py])                 │
│ - Runs in same Python environment                           │
│ - build123d library generates 3D geometry                  │
│ - Exports STL file                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Check Result                                        │
│ - If STL file exists → Success!                             │
│ - If error → Retry with error feedback (up to 3 times)      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: Return to Frontend                                  │
│ - Read STL file as binary                                   │
│ - Base64 encode                                             │
│ - Send via Socket.IO 'cad_data' event                       │
│ - Frontend displays in Three.js viewer                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Technologies

**1. build123d Library**
- Modern Python CAD library (replacement for OpenSCAD)
- Uses context managers for building geometry
- Example:
  ```python
  with BuildPart() as part:
      Box(10, 10, 10)  # Creates a cube
      Fillet(part.edges(), radius=1)  # Rounds edges
  
  result_part = part.part
  export_stl(result_part, 'output.stl')
  ```

**2. Gemini 3 Pro**
- Used specifically for code generation
- Has detailed system instruction about build123d
- Can fix errors through retry loop

**3. Error Handling & Retry**
```python
# If code fails:
1. Capture error message
2. Send error back to Gemini: "Your code failed with: [error]"
3. Gemini generates fixed code
4. Retry execution
5. Up to 3 attempts
```

### Why This Approach?

✅ **Flexibility**: Gemini can generate any geometry, not limited to templates  
✅ **Accuracy**: Code execution ensures correct geometry  
✅ **Local**: No cloud rendering, works offline (after code generation)  
✅ **Iterative**: Can fix errors automatically  

### Iteration Process

When user says "make it taller":

```
1. Read existing current_design.py
2. Send to Gemini: "Modify this code to make it taller"
3. Gemini generates updated code
4. Execute new code
5. Generate new STL
6. Display updated model
```

---

## 🔍 Tool Routing Logic

All tool routing happens in `TARS.py` `receive_audio()` method:

```python
# Line 844: Check if tool is in our list
if fc.name in ["generate_cad", "run_web_agent", ...]:
    
    # Line 848: Check permissions
    confirmation_required = self.permissions.get(fc.name, True)
    
    # Line 872+: Route to handler
    if fc.name == "generate_cad":
        asyncio.create_task(self.handle_cad_request(prompt))
    
    elif fc.name == "run_web_agent":
        asyncio.create_task(self.handle_web_agent_request(prompt))
    
    elif fc.name == "control_light":
        success = await self.kasa_agent.turn_on(target)
    
    # ... etc
```

**Key Point:** Each tool has a specific handler that calls the appropriate agent method.

---

## 📝 Summary

1. **Decision Making**: Gemini AI reads tool descriptions and matches user requests to tools
2. **User Flow**: Input → Server → Gemini → Tool Call → Agent → Result → Response
3. **Agents**: Async classes that execute specific tasks (CAD, Web, Printer, etc.)
4. **Web Agent**: Uses Gemini Computer Use + Playwright for autonomous browser control
5. **CAD Agent**: Uses Gemini to generate build123d code, executes locally to create STL files

The system is designed so **Gemini does the thinking**, and **agents do the doing**!


