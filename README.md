# 🌀 Blender Batch Render

📘 This README is also available in [Ukrainian](./README_UA.md)

**Blender Batch Render** is a desktop Python application with a GUI for batch rendering `.blend` files in Blender. It simplifies the workflow for 3D artists, animators, and tech artists who frequently work with multiple Blender projects.

![Application Interface](https://github.com/user-attachments/assets/41134de2-52ec-4cee-9308-5a7e0bc299d1)


## 🔧 Problem It Solves

Blender has no built-in support for rendering multiple `.blend` files sequentially. This app automates the process, tracks rendering progress per file, displays time spent, and lets you stop rendering at any moment.

## ✨ Key Features

- ✅ Batch rendering of `.blend` files using individual settings from each file.
- ⏱ Progress tracking in both frames and percentages.
- 🕒 Elapsed time shown for each rendered file.
- 💬 Real-time Blender console output inside the GUI.
- 🔎 Custom path to Blender executable (e.g., Steam version).
- 📂 Simple file list management: add, remove, clear.

## 🚀 How to Use

1. Make sure you have Python 3.6+ with `tkinter` installed.
2. Run `blender_batch_render.pyw`.
3. Add `.blend` files and set Blender's path.
4. Click **“Start Render”** and monitor the process!

## 📄 License

MIT — free to use, share, and improve.
