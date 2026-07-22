# Build the custom presentation inside Gradio

SetScout will retain Gradio Blocks as its application shell and use a custom HTML/CSS/JavaScript component for the Stage timeline, transitions, Run Summary, Recovery View, and structured Results. This provides control over interaction and visual design without introducing a separate frontend application and API deployment boundary.

## Considered Options

- Use only native Gradio components, which minimizes custom frontend code but limits visual and interaction control.
- Add a custom presentation component inside Gradio, which preserves the Python application boundary while enabling the intended experience.
- Build a separate frontend application, which maximizes control but adds API, state synchronization, and deployment complexity.
