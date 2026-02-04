import sys
import os
import logging
import tkinter as tk

# DEBUG: Log to file for EXE debugging
DEBUG_LOG = os.path.join(os.path.dirname(__file__), 'debug_startup.log')
def debug_log(msg):
    with open(DEBUG_LOG, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

debug_log("=== STARTUP BEGIN ===")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def global_tk_exception_handler(type, value, traceback):
    msg = str(value)
    debug_log(f"TK EXCEPTION: {type.__name__}: {msg}")
    if 'invalid command name' in msg or 'bad window path name' in msg:
        return
    sys.__excepthook__(type, value, traceback)

tk.Tk.report_callback_exception = staticmethod(global_tk_exception_handler)

def main():
    import time
    import customtkinter as ctk
    try:
        from edmrn.splash import SplashScreen
        debug_log("[OK] SplashScreen imported")
    except Exception as e:
        debug_log(f"[FAIL] SplashScreen import failed: {e}")
        raise
    t0 = time.time()
    print("=" * 60)
    print("ED Multi Route Navigation (EDMRN)")
    print("=" * 60)
    t1 = time.time(); print(f"[STARTUP] Banner printed in {t1-t0:.3f} s")
    root = ctk.CTk()
    root.withdraw()
    splash = SplashScreen(master=root)
    splash.update()
    import threading
    def load_app():
        try:
            from edmrn.app import EDMRN_App
            t2 = time.time(); print(f"[STARTUP] EDMRN_App imported in {t2-t1:.3f} s")
            app = EDMRN_App(root=root)
            t3 = time.time(); print(f"[STARTUP] EDMRN_App instance created in {t3-t2:.3f} s")
            def on_ready():
                splash.destroy()
                root.deiconify()
                try:
                    app.run()
                except Exception as e:
                    import traceback
                    with open("edmrn_crash.log", "a", encoding="utf-8") as f:
                        f.write("\n--- EDMRN Mainloop Crash ---\n")
                        f.write(traceback.format_exc())
                    print("An unexpected error occurred! Details have been saved to edmrn_crash.log.")
                    raise
                t4 = time.time(); print(f"[STARTUP] app.run() returned in {t4-t3:.3f} s")
            root.after(0, on_ready)
        except Exception as e:
            print(f"\n[ERROR] Application could not be started: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    threading.Thread(target=load_app, daemon=True).start()
    root.mainloop()
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
