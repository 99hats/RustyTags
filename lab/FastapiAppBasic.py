from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from rusty_tags import *
from rusty_tags import Section as HTMLSection
from rusty_tags.utils import create_template
from rusty_tags.datastar import Signals, DS
from rusty_tags.events import event, emit_async, on, ANY
from rusty_tags.client import Client
from rusty_tags.starlette import *
from rusty_tags.components import Button, Icon
from datastar_py.fastapi import  ReadSignals
from datastar_py.consts import ElementPatchMode
from uuid import uuid4
from typing import Any

hdrs = (Link(rel='stylesheet', href='https://unpkg.com/open-props'),
    # Link(rel='stylesheet', href='https://unpkg.com/open-props/normalize.min.css'),
    Link(rel='stylesheet', href='https://unpkg.com/open-props/buttons.min.css'),
    Style("""
    html {
        background: light-dark(var(--gradient-5), var(--gradient-16));
        min-height: 100vh;
        color: light-dark(var(--gray-9), var(--gray-1));
        font-family: var(--font-geometric-humanist);
        font-size: var(--font-size-3);
    }
    main {
        width: min(100% - 2rem, 50rem);
        margin-inline: auto;
    }
    """)
)
htmlkws = dict(lang="en")
bodykws = dict(signals=Signals(message="", conn=""))
page = create_template(hdrs=hdrs, htmlkw=htmlkws, bodykw=bodykws)

app = FastAPI()

def Section(title, *content):
    return HTMLSection(
        H2(title),
        *content,
        cls="fluid-flex"
    )

@app.get("/")
@page(title="FastAPI App", wrap_in=HTMLResponse)
def index():
    return Main(
            H1("Rusty Tags"),
            P("A high-performance HTML generation library that combines Rust-powered performance with modern Python web development."),
            Section("What Rusty Tags Does",
                P("Rusty Tags generates HTML and SVG content programmatically with:"),
                Ul(
                    Li("⚡ Rust Performance: 3-10x faster than pure Python with memory optimization, caching, and thread-local pools"),
                    Li("🆕 Automatic Mapping Expansion: Dictionaries automatically expand as tag attributes - `Div(\"text\", {\"id\": \"main\"})`"),
                    Li("🏗️ FastHTML-Style Syntax: Callable chaining support - `Div(cls=\"container\")(P(\"Hello\"), Button(\"Click\"))`"),
                    Li("⚡ Datastar Integration: Complete reactive web development with shorthand attributes (`signals`, `show`, `on_click`)"),
                    Li("🎨 Full-Stack Utilities: Page templates, decorators, and framework integrations (FastAPI, Flask, Django)"),
                    Li("🔧 Smart Type System: Native support for `__html__()`, `_repr_html_()`, `render()` methods and automatic type conversion"),
                    Li("📦 Complete HTML5/SVG: All standard tags plus custom tag creation with dynamic names"),
                ),
            ),
            
            Section("Component Demos",
                P("Test the RustyTags components:"),
                Ul(
                    Li(A("Button Component Demo", href="/components/button", cls="color-blue-6 text-decoration-underline")),
                ),
            ),
            
            signals=Signals(message=""),
        )


@app.get("/components/button")
@page(title="Button Component Demo", wrap_in=HTMLResponse)
def button_demo():
    return Main(
        H1("Button Component Demo"),
        P("Testing the Button component with different styles and interactions."),
        
        Section("Basic Buttons",
            P("Plain buttons without styling:"),
            Div(
                Button(Icon("home"), "Basic Button"),
                " ",
                Button("Disabled Button", disabled=True),
                " ",
                Button("Submit Button", type="submit"),
                cls="flex gap-2 flex-wrap"
            ),
        ),
        
        Section("Open Props Styled Buttons",
            P("Using Open Props classes for styling:"),
            Div(
                Button("Primary", cls="surface-1 px-3 py-2 border-radius-2 font-weight-6 color-0 bg-blue-6 border-0 cursor-pointer transition"),
                " ",
                Button("Secondary", cls="surface-1 px-3 py-2 border-radius-2 font-weight-6 color-0 bg-gray-6 border-0 cursor-pointer transition"),
                " ",
                Button("Success", cls="surface-1 px-3 py-2 border-radius-2 font-weight-6 color-0 bg-green-6 border-0 cursor-pointer transition"),
                " ",
                Button("Danger", cls="surface-1 px-3 py-2 border-radius-2 font-weight-6 color-0 bg-red-6 border-0 cursor-pointer transition"),
                cls="flex gap-2 flex-wrap"
            ),
        ),
        
        Section("Interactive Buttons with Datastar",
            P("Buttons that interact with Datastar signals:"),
            Div(
                Button("Click Me!", 
                       on_click="$message = 'Button was clicked!'",
                       cls="surface-1 px-4 py-2 border-radius-2 font-weight-6 color-0 bg-blue-6 border-0 cursor-pointer transition"),
                " ",
                Button("Reset Message", 
                       on_click="$message = ''",
                       cls="surface-1 px-4 py-2 border-radius-2 font-weight-6 color-0 bg-gray-6 border-0 cursor-pointer transition"),
                cls="flex gap-2"
            ),
            Div(
                P(f"Message: ", Span("$message", cls="font-weight-6")),
                cls="mt-4 p-3 border-radius-2 surface-2"
            ),
        ),
        
        Section("Form Buttons",
            P("Different button types for forms:"),
            Form(
                Div(
                    Button("Submit Form", type="submit", cls="surface-1 px-4 py-2 border-radius-2 font-weight-6 color-0 bg-green-6 border-0 cursor-pointer"),
                    " ",
                    Button("Reset Form", type="reset", cls="surface-1 px-4 py-2 border-radius-2 font-weight-6 color-0 bg-orange-6 border-0 cursor-pointer"),
                    " ",
                    Button("Cancel", type="button", cls="surface-1 px-4 py-2 border-radius-2 font-weight-6 color-0 bg-gray-6 border-0 cursor-pointer"),
                    cls="flex gap-2"
                ),
                cls="mt-2"
            ),
        ),
        
        Div(
            A("← Back to Home", href="/", cls="color-blue-6 text-decoration-underline"),
            cls="mt-8"
        ),
        
        signals=Signals(message=""),
    )


@app.get("/cmds/{command}/{sender}")
@datastar_response
async def commands(command: str, sender: str, request: Request, signals: ReadSignals):
    """Trigger events and broadcast to all connected clients"""
    signals = Signals(signals) if signals else {}
    backend_signal = event(command)
    await emit_async(backend_signal, sender, signals=signals, request=request)

@app.get("/updates")
@datastar_response
async def event_stream(request: Request, signals: ReadSignals):
    """SSE endpoint with automatic client management"""
    with Client(topics=["updates"]) as client:
        async for update in client.stream():
            yield update
    
@on("message.send")
async def notify(sender, request: Request, signals: Signals):
    message = signals.message or "No message provided" 
    yield sse_elements(Div(f"Server processed message: {message}", cls="text-lg text-bold mt-4 mt-2"),
                             selector="#updates", mode=ElementPatchMode.APPEND, topic="updates")
    yield sse_signals({"message": ""}, topic="updates")
    yield Notification(f"Server notification: {message}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("lab.FastapiAppBasic:app", host="0.0.0.0", port=8800, reload=True)



# @on(command, sender="user.global")
# def log(sender, request: Request, signals: dict | None):
#     message = (signals or {}).get("message", "No message provided")
#     print(f"Logging via 'log' handler: {message}")
#     return Notification(f"Logging via log handler: {message}")

# @on(command, sender="user.global")
# async def log_event(sender, request: Request, signals: dict | None):
#     message = (signals or {}).get("message", "No message provided")
#     print(f"Logging via 'log_event' handler: {message}")
#     return Notification(f"Logging via 'log_event' handler: {message}")




