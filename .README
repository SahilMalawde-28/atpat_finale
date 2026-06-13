# AI Tracking and Proctoring for Aptitude Tests (ATPAT)

ATPAT is a platform-agnostic, multi-modal examination integrity system[cite: 1]. By utilizing a lightweight Electron agent, it bypasses the vulnerabilities of traditional browser-based proctoring extensions to provide comprehensive, OS-level monitoring across learning management systems, web portals, and specialized coding environments[cite: 1].

## Key Features

*   **Platform Agnostic Execution:** Launches securely via a custom deep link URL scheme and monitors the entire desktop environment regardless of the underlying testing domain[cite: 1].
*   **Typing Integrity Module (TIM):** Intercepts global keystrokes to calculate a "Backspace Ratio," accurately distinguishing organic human typing from linear, copy-pasted input during technical assessments[cite: 1].
*   **Multi-Modal Threat Detection:** Operates concurrent real-time checks for missing faces, unauthorized mobile phones, window unfocus events, and suspicious background audio[cite: 1].
*   **Automated Admin Workflows:** Allows faculty to batch-enroll students via CSV and automatically dispatches time-limited, cryptographically secure assessment links via email[cite: 1].
*   **Unified Ethics Reporting:** Aggregates high-volume log data and media snippets into a centralized dashboard, generating a definitive, time-stamped "Ethics Score" report for each candidate[cite: 1].
*   **Network Resilience:** Features an offline-tolerance mechanism that buffers monitoring logs locally and attempts reconnection using an exponential backoff strategy[cite: 1].

## Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Client Agent** | Electron, TypeScript | Provides native OS-level hardware access and manages the Floating Proctor Box UI[cite: 1]. |
| **Backend API** | Python (Flask) | Operates as a lightweight microservice dedicated to high-concurrency log ingestion[cite: 1]. |
| **Database** | MongoDB & Firestore | Handles horizontal scaling for high-velocity time-series event data and robust RBAC rules[cite: 1]. |
| **AI Processing** | Client-Side Models | Executes vision and voice models locally on the GPU to eliminate server latency and bandwidth drag[cite: 1]. |

## System Architecture & Data Flow

1.  **Setup & Enrollment:** Administrators define test parameters and upload student metadata for bulk processing[cite: 1].
2.  **Authentication:** The server generates personalized JWT links and distributes them to students[cite: 1].
3.  **Active Proctoring:** The Electron agent initializes, enforcing a 3-Strike policy via a real-time Floating Proctor Box warning system[cite: 1].
4.  **Data Ingestion:** Hardware streams and TIM data are sent securely via HTTPS/TLS to the Python ingestion endpoint[cite: 1].
5.  **Data Aggregation:** The backend engine queries aggregated time-series data to compile structured output and flag priority review sessions[cite: 1].

## Future Roadmap

*   **Advanced Gaze Estimation:** Implement custom CNNs to accurately track consistent off-screen visual focus[cite: 1].
*   **Multi-Monitor Enforcement:** Utilize native OS APIs to actively detect and automatically disable secondary display outputs during an active session[cite: 1].
*   **Proactive Intervention Dashboard:** Build a real-time risk scoring console allowing human proctors to monitor multiple concurrent sessions and issue immediate warnings[cite: 1].
*   **Ambient Audio Classification:** Upgrade the VAD module to classify specific ambient sounds, differentiating between harmless background noise and active collusion[cite: 1].
