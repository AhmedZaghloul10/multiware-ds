# MultiWare DS — Setup Guide

## Option 1 — Python (easiest, no install needed)
```bash
cd multiware-ds
python -m http.server 3000
```
Then open: http://localhost:3000

## Option 2 — Node.js
```bash
cd multiware-ds
npm start
```
Then open: http://localhost:3000

## Option 3 — VS Code
1. Install the **Live Server** extension
2. Right-click `index.html` → **Open with Live Server**

## Option 4 — Just double-click
Open `index.html` directly in **Firefox** (works without a server).
Chrome may block it — use Firefox or one of the options above.

---

## Project Structure
```
multiware-ds/
├── index.html       ← Full app (all algorithms + UI in one file)
├── package.json     ← npm start script
└── README.md        ← This file
```

## What's inside index.html
- Real Dijkstra with MinHeap — builds cost matrix from live graph
- Real Kruskal with Union-Find — MST backbone animation
- Real DP Assignment — sparse state-space, full traceback
- Next-Fit + FFD bin packing — side-by-side comparison
- Interactive canvas — drag nodes, add warehouses/edges, edit stock
- 7 tabs: Network · Dijkstra · Kruskal · DP · Bin Packing · Compare · Orders
