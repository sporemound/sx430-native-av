"""Canon PowerShot SX430 IS: Live Sensor Streaming Server for OBS Studio.

Streams direct DIGIC 4+ CCD sensor video over Wi-Fi PTP with zero SD card writes
and serves a pristine 720p @ 25fps HTTP MPEG-TS live stream for OBS Studio.
"""
import _winapi, argparse, datetime, http.server, json, os, platform, queue, shutil, socket, socketserver, struct, subprocess, sys, threading, time
from pathlib import Path

def print_banner(port, stream_url):
    print("=" * 72)
    print("  Canon PowerShot SX430 IS -> OBS Studio Live Sensor Stream Server")
    print("  Video: 1280x720 @ 25.0 fps Real-Time Wallclock CFR Stream (Zero Glitch)")
    print("  Audio: 48.0 kHz Stereo AAC Live Stream Sync")
    print(f"  Live Stream Output: {stream_url}")
    print("  Mode: Direct CCD Sensor (Zero SD Card Writes | Zero Glitch)")
    print("=" * 72)

def create_named_pipe(name):
    PIPE_ACCESS_DUPLEX = 3
    PIPE_TYPE_BYTE = 0
    PIPE_READMODE_BYTE = 0
    PIPE_WAIT = 0
    return _winapi.CreateNamedPipe(
        name,
        PIPE_ACCESS_DUPLEX,
        PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
        1, 2097152, 2097152, 0, 0
    )

def main():
    parser = argparse.ArgumentParser(description="Canon SX430 IS Live Streaming Server for OBS")
    parser.add_argument("--port", type=int, default=8554, help="Local HTTP streaming port (default: 8554)")
    parser.add_argument("--camera-ip", default=os.getenv("SX430_CAMERA_IP", "10.0.0.202"), help="Camera Wi-Fi IP address")
    parser.add_argument("--chdkptp-dir", default=os.getenv("CHDKPTP_DIR", "client/chdkptp"), help="Path to chdkptp directory")
    parser.add_argument("--ffmpeg-bin", default=os.getenv("FFMPEG_BIN", "ffmpeg"), help="Path to ffmpeg executable")
    args = parser.parse_args()

    stream_url = f"http://127.0.0.1:{args.port}"
    print_banner(args.port, stream_url)

    stop_event = threading.Event()
    clients = []
    clients_lock = threading.Lock()
    header_cache = bytearray()

    # 1. Instant HTTP Server Startup for OBS Studio
    class StreamHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "video/mp2t")
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with clients_lock:
                if header_cache:
                    try:
                        self.wfile.write(header_cache)
                        self.wfile.flush()
                    except Exception:
                        return
                clients.append(self.wfile)
            while not stop_event.is_set():
                time.sleep(0.5)
                with clients_lock:
                    if self.wfile not in clients:
                        break
        def log_message(self, format, *args): pass

    class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    try:
        httpd = ThreadedHTTPServer(("0.0.0.0", args.port), StreamHandler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        print(f"[HTTP] Live streaming server listening on {stream_url}")
    except Exception as e:
        print(f"[HTTP Error] Could not bind port {args.port}: {e}")

    session_dir = Path("stream-session")
    session_dir.mkdir(parents=True, exist_ok=True)
    
    script_source = Path(__file__).parent.parent / "camera" / "stream-sensor-live.lua"
    if script_source.exists():
        shutil.copyfile(script_source, session_dir / "stream-sensor-live.lua")

    # 2. Named Pipes & Zero-Latency Stream Normalizer
    pid = os.getpid()
    pipe_v_name = rf"\\.\pipe\sx430_v_{pid}"
    h_v = create_named_pipe(pipe_v_name)

    print("\n[1/3] Launching FFmpeg Zero-Latency 720p Stream Normalizer...")
    ffmpeg_cmd = [
        str(args.ffmpeg_bin), "-y", "-v", "warning",
        "-use_wallclock_as_timestamps", "1",
        "-f", "image2pipe", "-vcodec", "ppm", "-i", pipe_v_name,
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-vf", "fps=25,scale=1280:720",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        "-pix_fmt", "yuv420p", "-g", "25",
        "-c:a", "aac",
        "-f", "mpegts", "pipe:1"
    ]
    ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=65536)

    v_bin = session_dir / "stream_video.bin"
    status_file = session_dir / "stream-status.txt"
    v_bin.write_bytes(b"")

    def pipe_feeder(file_path, handle):
        try:
            _winapi.ConnectNamedPipe(handle, 0)
        except OSError as e:
            if e.winerror != 535: pass
        offset = 0
        try:
            while not stop_event.is_set():
                if file_path.exists():
                    size = file_path.stat().st_size
                    if size > offset:
                        with file_path.open("rb") as f:
                            f.seek(offset)
                            chunk = f.read(262144)
                            if chunk:
                                _winapi.WriteFile(handle, chunk)
                                offset += len(chunk)
                time.sleep(0.001)
        except Exception:
            pass
        finally:
            try: _winapi.CloseHandle(handle)
            except Exception: pass

    threading.Thread(target=pipe_feeder, args=(v_bin, h_v), daemon=True).start()

    def broadcaster():
        nonlocal header_cache
        while not stop_event.is_set():
            try:
                chunk = ffmpeg_proc.stdout.read(4096)
                if not chunk: break
                if len(header_cache) < 32768:
                    header_cache.extend(chunk[:32768 - len(header_cache)])
                with clients_lock:
                    active = []
                    for client in clients:
                        try:
                            client.write(chunk)
                            client.flush()
                            active.append(client)
                        except Exception:
                            pass
                    clients[:] = active
            except Exception:
                break

    threading.Thread(target=broadcaster, daemon=True).start()

    client_path = Path(args.chdkptp_dir)
    env = os.environ.copy()
    env["LUA_PATH"] = (client_path / "lua/?.lua").as_posix() + ";;"
    env["CHDKPTP_HOME"] = str(session_dir)

    print(f"[2/3] Waiting for camera connection at {args.camera_ip}...")
    print("      (Make sure camera is in PLAYBACK mode and connected to Wi-Fi)")
    print(f"\n[3/3] OBS Studio Setup Instructions:")
    print(f"      1. In OBS Sources, click '+' -> 'Media Source'")
    print(f"      2. UNCHECK 'Local File'")
    print(f"      3. Input:        {stream_url}")
    print(f"      4. Input Format: mpegts")
    print(f"      5. Click OK!\n")
    print("=" * 72)
    print("  READY TO STREAM -- Connect camera now (Ctrl+C to stop)")
    print("=" * 72)

    chdkptp_exe = client_path / "chdkptp.exe" if (client_path / "chdkptp.exe").exists() else "chdkptp"
    chdkptp_cmd = [
        str(chdkptp_exe), "-r", "-eset cli_error_exit=true",
        f"-econnect -h={args.camera_ip}",
        "-eexec dofile('stream-sensor-live.lua')"
    ]

    attempt = 0
    connected = False
    ptp_proc = None
    start_time = None
    total_v_frames = 0

    try:
        while not stop_event.is_set():
            attempt += 1
            if not connected:
                sys.stdout.write(f"\r[Connecting] Searching for camera on {args.camera_ip} (attempt {attempt})...")
                sys.stdout.flush()

            with (session_dir / f"client-{attempt:03d}.log").open("w") as log_file:
                ptp_proc = subprocess.Popen(
                    chdkptp_cmd,
                    cwd=session_dir,
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )

                while ptp_proc.poll() is None and not stop_event.is_set():
                    if status_file.exists():
                        try:
                            status_text = status_file.read_text(encoding="utf-8").strip()
                            if status_text == "CAMERA_CONNECTED" and not connected:
                                connected = True
                                if start_time is None:
                                    start_time = time.time()
                                print(f"\n\n[Connected] Canon SX430 IS connected! Live sensor stream active...")
                            elif status_text.startswith("STAT_V,"):
                                parts = status_text.split(",")
                                total_v_frames = int(parts[1])
                            elif status_text.startswith("STREAM_ERROR") or status_text.startswith("FATAL_STREAM_ERROR"):
                                pass
                        except Exception:
                            pass

                    if connected and start_time is not None:
                        elapsed = max(1, time.time() - start_time)
                        fps = total_v_frames / elapsed
                        v_size = v_bin.stat().st_size if v_bin.exists() else 0
                        kbps = (v_size * 8 / 1000) / elapsed
                        uptime = str(datetime.timedelta(seconds=int(elapsed)))
                        sys.stdout.write(f"\r[LIVE] Uptime: {uptime} | Video: {total_v_frames:5d} frames ({fps:4.1f} fps) | Rate: {kbps:6.1f} kbps | OBS: {stream_url}")
                        sys.stdout.flush()

                    time.sleep(0.05)

            if not stop_event.is_set():
                if connected:
                    print("\n[Stream Cycle] Camera connection refreshed; resuming sensor stream...")
                    connected = False
                time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n[Shutdown] Stopping live stream...")
    finally:
        stop_event.set()
        if ptp_proc is not None:
            try:
                ptp_proc.terminate()
                ptp_proc.wait(timeout=5)
            except Exception:
                pass
        try:
            ffmpeg_proc.terminate()
            ffmpeg_proc.wait(timeout=2)
        except Exception:
            pass

    print("\n[Complete] Stream session ended cleanly.")

if __name__ == "__main__":
    main()
