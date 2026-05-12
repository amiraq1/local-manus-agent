// Local Manus Agent - Tauri Desktop App
// Manages the Python backend lifecycle and opens the frontend in a native window.

#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::{Command, Child};
use std::sync::Mutex;
use tauri::Manager;

struct BackendProcess(Mutex<Option<Child>>);

fn start_backend() -> Option<Child> {
    // Try to find python in common locations
    let python_cmds = if cfg!(target_os = "windows") {
        vec!["python", "py", "python3"]
    } else {
        vec!["python3", "python"]
    };

    for py in &python_cmds {
        let result = Command::new(py)
            .args(["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"])
            .current_dir("../backend")
            .spawn();

        if let Ok(child) = result {
            println!("Backend started with {} (PID: {})", py, child.id());
            return Some(child);
        }
    }

    // Try relative to executable
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()));

    if let Some(dir) = exe_dir {
        let backend_dir = dir.join("../backend");
        if backend_dir.exists() {
            for py in &python_cmds {
                let result = Command::new(py)
                    .args(["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"])
                    .current_dir(&backend_dir)
                    .spawn();

                if let Ok(child) = result {
                    println!("Backend started from {:?} (PID: {})", backend_dir, child.id());
                    return Some(child);
                }
            }
        }
    }

    eprintln!("Warning: Could not start backend. Start it manually.");
    None
}

fn stop_backend(process: &Mutex<Option<Child>>) {
    if let Ok(mut guard) = process.lock() {
        if let Some(ref mut child) = *guard {
            println!("Stopping backend (PID: {})...", child.id());
            let _ = child.kill();
            let _ = child.wait();
            println!("Backend stopped.");
        }
        *guard = None;
    }
}

fn main() {
    let backend = start_backend();

    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(backend)))
        .on_window_event(|event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event.event() {
                let app = event.window().app_handle();
                let state = app.state::<BackendProcess>();
                stop_backend(&state.0);
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
