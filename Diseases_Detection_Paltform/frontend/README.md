# Frontend UI - Hybrid Quantum Machine Learning Platform

The frontend application provides researchers and medical professionals with a rich, interactive interface to manage biomedical datasets, configure quantum machine learning pipelines, and visualize diagnostic predictions.

## Architecture & Tech Stack

- **Core Library**: React 18
- **Language**: TypeScript for strict type safety and autocompletion
- **Build Tool**: Vite (Lightning fast HMR and optimized builds)
- **Styling**: TailwindCSS (Utility-first CSS framework for custom, premium aesthetics)
- **State Management**: Zustand (Lightweight, hook-based global state)
- **Routing**: React Router DOM (Client-side routing)
- **API Client**: Axios with automatic JWT interceptors
- **Data Visualization**: Recharts (for rendering loss curves, quantum node graphs, and confusion matrices)

## Implementation Details

The frontend is structured to cleanly separate UI components from business logic:

1. **Pages (`src/pages/`)**: Top-level route components. These assemble smaller components into complete views (e.g., `DashboardPage`, `DatasetUploadPage`, `QuantumConfigPage`).
2. **Components (`src/components/`)**: Reusable UI elements (Buttons, Modals, Forms). Strict adherence to Tailwind design tokens ensures a consistent, premium look and feel.
3. **Store (`src/store/`)**: Zustand stores manage global application state, primarily user authentication (`useAuthStore`) and active ML experiment tracking.
4. **API (`src/api/`)**: Centralized Axios client configured with base URLs and JWT bearer token injection. All backend communication goes through this layer.

### Step-by-Step UI Flow

1. **Authentication**: Users log in via the `/login` route. Upon success, a JWT is stored securely, and the Axios interceptor begins attaching it to all subsequent requests.
2. **Dashboard**: Users land on the Dashboard, viewing high-level metrics of their datasets and trained models.
3. **Dataset Pipeline**:
   - The user navigates to `/datasets/new` and uploads a CSV file.
   - The UI polls the backend for the dataset analysis.
   - The Ollama Preprocessing Agent presents a suggested cleaning strategy in the UI. The user accepts or modifies it.
4. **Quantum Configuration**:
   - In `/models/new`, the user selects features, sets the target variable (e.g., "Lung Cancer Diagnosis"), and toggles "Quantum Mode".
   - A specialized UI panel opens to select Qubit counts, Ansatz type, and Embedding strategy.
5. **Real-time Training**: Once training starts, the UI connects to the backend and renders a live chart of the VQC loss function using Recharts.
6. **Results & Explainability**: The trained model view displays the accuracy, F1-score, and a detailed breakdown of feature importance, helping doctors understand the prediction.

## Configuration

The frontend relies on environment variables to locate the backend API.

Create a `.env` file in the `frontend/` directory (for local Vite development):

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## How to Run (With Docker)

The frontend is meant to be run via the root `docker-compose.yml`. In production, the Dockerfile builds the static assets and serves them via Nginx.

To run the frontend individually via Docker:

```bash
cd frontend
docker build -t hybrid_qml_frontend .
docker run -p 3000:80 hybrid_qml_frontend
```

## How to Run (Local Development)

If you wish to run the frontend locally with Hot Module Replacement (HMR) for active development:

```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:5173`. Ensure your backend server is also running locally on port 8000.
