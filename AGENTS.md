# Engineering notes

This repository implements a receive-only ESP32-C5 UART capture tool.
Treat physical flashing, wiring and changes to host tooling as separately
authorized operations. Do not presume vendor pin mapping based on a
compatible third-party firmware binary.

Keep UART1 RX input-only and output over native USB Serial/JTAG. Keep
protocol framing and host decoding in sync; run host tests and a native
ESP32-C5 target build before making readiness claims. Preserve raw capture
bytes and disclose dropped/corrupt frames. Keep the application independent
of StickShift. No radio, display, network or persistent storage scope in v0.1.
