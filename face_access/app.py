import streamlit as st
from main import FaceAccessSystem
import tempfile
import os

st.set_page_config(
    page_title="Face Access System",
    layout="centered"
)

# ===== INIT SYSTEM SEKALI =====
if "system" not in st.session_state:
    st.session_state.system = FaceAccessSystem()

# ===== INIT SESSION STATE =====
if "page" not in st.session_state:
    st.session_state.page = "home"

system = st.session_state.system

st.title("🔐 Face Access System")

# ===== MENU =====
menu = st.radio(
    "Pilih Menu",
    ["🏠 Home", "📝 Pendaftaran Pegawai", "🚪 Face Recognition", "👥 Crowd Recognition"],
    horizontal=True
)

if menu == "🏠 Home":
    st.session_state.page = "home"

elif menu == "📝 Pendaftaran Pegawai":
    st.session_state.page = "enrollment"

elif menu == "🚪 Face Recognition":
    st.session_state.page = "recognition"

elif menu == "👥 Crowd Recognition":
    st.session_state.page = "crowd"

# ===== HOME =====
if st.session_state.page == "home":
    st.info("### Selamat datang di Face Access System")
    st.write("- **📝 Pendaftaran Pegawai**")
    st.write("- **🚪 Face Recognition (Akses Pintu)**")
    st.write("- **👥 Crowd Recognition (Video/CCTV)**")

# ===== ENROLLMENT PAGE =====
if st.session_state.page == "enrollment":
    st.header("📝 Pendaftaran Pegawai Baru")
    
    # METODE DIPILIH DI LUAR FORM - agar re-render langsung
    st.divider()
    st.subheader("Data Pegawai")
    nama = st.text_input("Nama Lengkap", max_chars=100, key="emp_name")
    nip = st.text_input("NIP (10 digit)", max_chars=10, key="emp_nip")
    st.divider()
    
    st.subheader("Pilih Metode Pendaftaran")
    
    metode = st.radio(
        "Metode:",
        ["Upload Gambar", "Rekam Video (Webcam)"],
        key="enrollment_method",
        horizontal=True
    )
    
    st.divider()
    
    # ===== UPLOAD GAMBAR =====
    if metode == "Upload Gambar":
        st.subheader("📸 Upload Foto Wajah")
        st.info("Silakan upload 5-10 foto wajah dengan angle dan ekspresi berbeda")
        
        # Init session state untuk track delete
        if "should_clear_uploader" not in st.session_state:
            st.session_state.should_clear_uploader = False
        
        # Callback untuk delete all
        def clear_uploader():
            st.session_state.should_clear_uploader = True
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Pilih gambar (JPG, JPEG, PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="enrollment_images"
        )
        
        # Reset flag setelah widget render
        if st.session_state.should_clear_uploader:
            st.session_state.should_clear_uploader = False
        
        if uploaded_files:
            # Status & actions
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if len(uploaded_files) < 5:
                    st.warning(f"⚠️ {len(uploaded_files)} gambar. Minimal 5 diperlukan!")
                else:
                    st.success(f"✅ {len(uploaded_files)} gambar siap")
            
            # Preview thumbnails
            st.subheader("Preview")
            
            # Display in 4 columns
            cols = st.columns(4)
            for idx, file in enumerate(uploaded_files):
                with cols[idx % 4]:
                    # Display thumbnail
                    st.image(file, width='stretch')
                    # Display filename (truncated)
                    filename = file.name if len(file.name) <= 20 else file.name[:17] + "..."
                    st.caption(filename)
            st.divider()            
        with st.form("enrollment_form_upload", border=True):         
            submitted = st.form_submit_button(
                "🚀 Mulai Pendaftaran",
                type="primary",
                width='stretch'
            )

            if submitted:
                # Validate inputs
                if not nama or not nip:
                    st.error("❌ Nama dan NIP wajib diisi!")
                elif len(nip) != 10:
                    st.error("❌ NIP harus 10 digit!")
                elif not uploaded_files or len(uploaded_files) < 5:
                    st.error("❌ Minimal 5 gambar diperlukan untuk pendaftaran!")
                else:
                    st.divider()
                    st.subheader("⏳ Memproses upload dan mendaftarkan...")
                    try:
                        import tempfile
                        import shutil

                        temp_dir = tempfile.mkdtemp()
                        paths = []

                        for f in uploaded_files:
                            # Save uploaded file to temp dir
                            safe_name = f.name
                            dest = os.path.join(temp_dir, safe_name)
                            with open(dest, "wb") as out:
                                out.write(f.read())
                            paths.append(dest)

                        # Validate each image and show result to user
                        st.subheader("Hasil Validasi Gambar")
                        cols = st.columns(4)
                        valid_count = 0

                        for i, p in enumerate(paths):
                            with cols[i % 4]:
                                st.image(p, width='stretch')
                                try:
                                    import cv2
                                    frame = cv2.imread(p)
                                    if frame is None:
                                        st.error("✗ Gagal membaca gambar")
                                        continue

                                    face, msg_face = system.detector.get_single_face(frame, system.settings.CONFIDENCE_THRESHOLD)
                                    if face is None:
                                        st.error(f"✗ {msg_face}")
                                        continue

                                    is_valid, result = system.quality_checker.validate_face(frame, face)
                                    if is_valid:
                                        st.success("✓ Valid: wajah terdeteksi & quality OK")
                                        valid_count += 1
                                    else:
                                        st.warning(f"✗ Tidak valid: {result}")

                                except Exception as e:
                                    st.error(f"Error saat validasi: {e}")

                        # If not enough valid images, abort early with message
                        if valid_count < 5:
                            st.error(f"❌ Hanya {valid_count} gambar valid. Minimal 5 gambar valid diperlukan untuk pendaftaran.")
                            success = False
                        else:
                            # Call enrollment with uploaded image paths
                            success = system.enroll_employee(nama=nama, nip=nip, mode='upload', image_paths=paths)

                        if success:
                            st.success("✅ Pendaftaran berhasil!")
                            st.info(f"**Pegawai berhasil terdaftar:**\n- Nama: {nama}\n- NIP: {nip}\n- Metode: Upload Gambar")
                            # Clear uploader for convenience
                            st.session_state.should_clear_uploader = True
                        else:
                            st.error("❌ Pendaftaran gagal!")
                            st.warning("Tips: Pastikan pencahayaan cukup dan gambar jelas")

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        with st.expander("Detail Error"):
                            import traceback
                            st.code(traceback.format_exc())
                    finally:
                        # Cleanup temp files if they exist
                        try:
                            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                                shutil.rmtree(temp_dir)
                        except Exception:
                            pass
    
    # ===== REKAM VIDEO =====
    elif metode == "Rekam Video (Webcam)":
        st.subheader("🎥 Rekam Menggunakan Webcam")
        st.info("Sistem akan merekam 10 sampel wajah otomatis")
        
        st.markdown("""
        **Petunjuk:**
        1. Pastikan webcam sudah terhubung
        2. Posisikan wajah di depan kamera
        3. Variasikan angle dan ekspresi wajah (angguk, pandang kanan-kiri)
        4. Proses rekam ~ 30-60 detik
        5. Sistem akan otomatis mengambil 10 sampel terbaik
        """)
        
        # FORM DATA PEGAWAI
        st.divider()            
        with st.form("enrollment_form_video", border=True):         
            submitted = st.form_submit_button(
                "🚀 Mulai Pendaftaran",
                type="primary",
                width='stretch'
            )
            
            if submitted:
                if not nama or not nip:
                    st.error("❌ Nama dan NIP wajib diisi!")
                elif len(nip) != 10:
                    st.error("❌ NIP harus 10 digit!")
                else:
                    st.divider()
                    st.subheader("⏳ Proses Perekaman")
                    
                    with st.spinner("⏳ Membuka webcam..."):
                        try:
                            st.warning("🎥 Webcam sedang membuka. Ikuti instruksi di window yang muncul.")
                            st.info("💡 Tekan 'q' untuk membatalkan rekaman")
                            
                            success = system.enroll_employee(
                                nama=nama,
                                nip=nip,
                                mode="video"
                            )
                            
                            if success:
                                st.success("✅ Pendaftaran berhasil!")
                                st.info(f"""
                                **Pegawai berhasil terdaftar:**
                                - Nama: {nama}
                                - NIP: {nip}
                                - Metode: Rekam Video
                                """)
                            else:
                                st.error("❌ Pendaftaran gagal!")
                                st.warning("Tips: Pastikan pencahayaan cukup dan wajah terlihat dengan jelas")
                                
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            with st.expander("Detail Error"):
                                import traceback
                                st.code(traceback.format_exc())

# ===== RECOGNITION PAGE =====
elif st.session_state.page == "recognition":
    st.header("🚪 Face Recognition - Akses Pintu")
    
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Langkah-langkah:")
        st.markdown("""
        1. Klik tombol **Mulai Recognition**
        2. Posisikan wajah di depan kamera
        3. Sistem akan otomatis verifikasi
        4. Pintu terbuka jika pengenalan berhasil
        """)
    
    with col2:
        st.info("""
        ⏱️ **Timeout:** 15 detik
        
        🔄 **Max Attempts:** 3x
        
        ⏸️ **Cooldown:** 5 detik
        """)
    
    st.divider()
    
    if st.button("🚀 Mulai Recognition", type="primary", width='stretch', key="recognition_btn"):
        try:
            with st.spinner("⏳ Membuka webcam..."):
                st.info("🎥 Webcam sedang dibuka. Posisikan wajah Anda di depan kamera.")
                
                emp_id = system.recognize_face()

            if emp_id:
                # Ambil data pegawai dari repository
                try:
                    peg = system.pegawai_repo.get_by_id(emp_id)
                    nama_user = peg.get('nama') if peg else "Pengguna"
                except Exception:
                    nama_user = "Pengguna"

                st.success("✅ AKSES DIBERIKAN!")
                st.success(f"🚪 Pintu terbuka, Selamat datang {nama_user}!")
            else:
                st.error("❌ AKSES DITOLAK!")
                st.error("Wajah tidak dikenali atau tidak terdaftar")
                
                with st.container(border=True):
                    st.markdown("""
                    **Kemungkinan penyebab:**
                    - Wajah belum terdaftar di sistem
                    - Kualitas gambar buruk (terlalu gelap/blur)
                    - Pencahayaan tidak optimal
                    - Wajah tidak terdeteksi dengan jelas
                    
                    **Solusi:**
                    1. Pastikan pencahayaan cukup
                    2. Posisikan wajah lebih dekat ke kamera
                    3. Cek apakah wajah sudah terdaftar
                    4. Coba lagi dalam beberapa detik
                    """)
                    
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            with st.expander("Detail Error"):
                import traceback
                st.code(traceback.format_exc())
                
# ===== CROWD RECOGNITION =====
elif st.session_state.page == "crowd":
    st.header("👥 Crowd Recognition (Video / CCTV)")

    video_source = st.text_input("Path video atau 0 untuk webcam", value="0")
    output_video = st.text_input("Path output video (opsional)")
    is_outdoor = st.checkbox("Outdoor")
    sample_fps = st.number_input("Durasi Rekaman", min_value=1, max_value=30, value=5)

    if st.button("🚀 Mulai Crowd Detection"):
        if video_source == "0":
            video_source = 0

        output_path = output_video if output_video else None

        with st.spinner("Memproses video..."):
            summary = system.recognize_from_crowd_video(
                video_source=video_source,
                output_path=output_path,
                is_outdoor=is_outdoor,
                sample_fps=sample_fps
            )

        if summary:
            st.success("Proses selesai")
            st.write(f"Total Frame: {summary['total_frames']}")
            st.write(f"Unique People: {summary['unique_people']}")

            if summary["people"]:
                st.subheader("Orang Terdeteksi")
                for p in summary["people"]:
                    st.write(f"- {p['nama']} (NIP: {p['nip']}) muncul {p['count']}x")

            if st.button("💾 Simpan Report"):
                report_path = st.text_input("Path report (.txt)", value="crowd_report.txt")
                system.crowd_detector.generate_detection_report(summary, report_path)
                st.success("Report disimpan")
