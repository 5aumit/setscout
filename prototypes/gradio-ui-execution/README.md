# SetScout execution and Results UX — throwaway prototype

This is a disposable visual prototype. It does not use the SetScout pipeline,
network calls, credentials, or persistence.

It answers one question: **which composition and completion transition best
communicates a live SetScout Run without competing with Results?**

Run it with:

```bash
./scripts/run_gradio_ui_prototype.sh
```

Then open the printed local address. The floating control tray switches among
the three directions and replays five fake Run Event scenarios. Use URL search
parameters to share a view, for example `?variant=fold&scenario=limited`.
For the fixed, side-by-side comparison gallery, open `/gallery.html`.

Directions:

- **Ledger** — an explicit vertical Stage rail; Results take the main panel.
- **Signal** — sparse top telemetry; the active Stage is the page’s focal point.
- **Fold** — execution begins as a full sheet and visibly folds into a compact Run Summary.

Check the light/dark override, narrow layout, and your operating system’s
reduced-motion setting before choosing a direction.
