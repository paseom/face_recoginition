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

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = None

system = st.session_state.system

st.title("🔐 Face Access System")

# ===== MENU =====
menu = st.radio(
    "Pilih Menu",
    ["🏠 Home", "📝 Pendaftaran Pegawai", "🚪 Face Recognition"],
    horizontal=True
)

if menu == "🏠 Home":
    st.session_state.page = "home"
    st.info("### Selamat datang di Face Access System")
    st.write("Pilih menu di atas untuk memulai:")
    st.write("- **📝 Pendaftaran Pegawai**: Daftarkan wajah pegawai baru")
    st.write("- **🚪 Face Recognition**: Verifikasi akses dengan face recognition")

elif menu == "📝 Pendaftaran Pegawai":
    st.session_state.page = "enrollment"

elif menu == "🚪 Face Recognition":
    st.session_state.page = "recognition"

# ===== ENROLLMENT PAGE =====
if st.session_state.page == "enrollment":
    st.header("📝 Pendaftaran Pegawai Baru")
    
    with st.form("enrollment_form"):
        st.subheader("Data Pegawai")
        
        nama = st.text_input("Nama Lengkap", placeholder="Contoh: John Doe")
        nip = st.text_input("NIP (10 digit)", max_chars=10, placeholder="1234567890")
        
        st.divider()
        st.subheader("Metode Pendaftaran")
        
        metode = st.radio(
            "Pilih metode:",
            ["Upload Gambar", "Rekam Video (Webcam)"],
            help="Upload Gambar: Siapkan 5-10 foto wajah\nRekam Video: Menggunakan webcam real-time"
        )
        
        uploaded_files = None
        
        if metode == "Upload Gambar":
            st.info("📸 Upload 5-10 foto wajah dengan angle & ekspresi berbeda")
            
            uploaded_files = st.file_uploader(
                "Pilih gambar (JPG, JPEG, PNG)",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                help="Tekan Ctrl+Click untuk pilih multiple files"
            )
            
            if uploaded_files:
                if len(uploaded_files) < 5:
                    st.warning(f"⚠️ Hanya {len(uploaded_files)} gambar. Minimal 5 gambar diperlukan!")
                else:
                    st.success(f"✅ {len(uploaded_files)} gambar siap diproses")
                    
                    # Preview uploaded files
                    with st.expander("📋 Lihat file yang diupload"):
                        cols = st.columns(3)
                        for idx, file in enumerate(uploaded_files):
                            with cols[idx % 3]:
                                st.image(file, caption=file.name, use_container_width=True)
        
        else:  # Rekam Video
            st.warning("⚠️ Webcam akan diaktifkan setelah klik tombol di bawah")
        
        st.divider()
        
        # Submit button
        submitted = st.form_submit_button(
            "🚀 Mulai Pendaftaran",
            type="primary",
            use_container_width=True
        )
    
    # ===== PROCESS SETELAH SUBMIT =====
    if submitted:
        # Validasi input
        if not nama or not nip:
            st.error("❌ Nama dan NIP wajib diisi!")
            st.stop()
        
        if len(nip) != 10:
            st.error("❌ NIP harus 10 digit!")
            st.stop()
        
        if metode == "Upload Gambar":
            if not uploaded_files:
                st.error("❌ Belum ada gambar yang diupload!")
                st.stop()
            
            if len(uploaded_files) < 5:
                st.error(f"❌ Minimal 5 gambar diperlukan! Saat ini hanya {len(uploaded_files)} gambar")
                st.stop()
            
            # Process uploaded images
            with st.spinner("⏳ Memproses gambar..."):
                # Create temp directory
                temp_dir = tempfile.mkdtemp()
                
                # Save uploaded files to temp directory
                image_paths = []
                for file in uploaded_files:
                    file_path = os.path.join(temp_dir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    image_paths.append(file_path)
                
                st.info(f"📁 {len(image_paths)} gambar disimpan di temporary folder")
                
                # Store in session state for enrollment process
                st.session_state.temp_dir = temp_dir
                st.session_state.uploaded_image_paths = image_paths
                
                # Call enrollment with upload mode
                try:
                    success = system.enroll_employee(
                        nama=nama,
                        nip=nip,
                        mode="upload",
                        image_paths=image_paths  # Pass paths directly
                    )
                    
                    if success:
                        st.success("✅ Pendaftaran berhasil!")
                        st.balloons()
                        
                        # Show success info
                        st.info(f"""
                        **Pegawai berhasil terdaftar:**
                        - Nama: {nama}
                        - NIP: {nip}
                        - Metode: Upload Gambar
                        - Jumlah foto: {len(uploaded_files)}
                        """)
                        
                        # Cleanup temp files
                        import shutil
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            pass
                        
                        # Reset session state
                        st.session_state.temp_dir = None
                        st.session_state.uploaded_image_paths = []
                    else:
                        st.error("❌ Pendaftaran gagal! Cek kualitas gambar dan coba lagi.")
                        st.warning("Tips: Pastikan semua foto jelas, tidak blur, dan wajah terlihat dengan baik")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("Detail Error"):
                        st.code(traceback.format_exc())
        
        else:  # Rekam Video
            with st.spinner("⏳ Membuka webcam..."):
                try:
                    st.warning("🎥 Webcam akan terbuka. Ikuti instruksi di window yang muncul.")
                    st.info("💡 Tekan 'q' untuk membatalkan")
                    
                    success = system.enroll_employee(
                        nama=nama,
                        nip=nip,
                        mode="video"
                    )
                    
                    if success:
                        st.success("✅ Pendaftaran berhasil!")
                        st.balloons()
                        
                        st.info(f"""
                        **Pegawai berhasil terdaftar:**
                        - Nama: {nama}
                        - NIP: {nip}
                        - Metode: Rekam Video
                        """)
                    else:
                        st.error("❌ Pendaftaran gagal!")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ===== RECOGNITION PAGE =====
elif st.session_state.page == "recognition":
    st.header("🚪 Face Recognition - Akses Pintu")
    
    st.info("### Instruksi:")
    st.write("1. Klik tombol **Mulai Recognition** di bawah")
    st.write("2. Webcam akan terbuka")
    st.write("3. Posisikan wajah Anda di depan kamera")
    st.write("4. Ikuti instruksi liveness check")
    st.write("5. Sistem akan verifikasi identitas Anda")
    
    st.warning("⚠️ Webcam akan diaktifkan setelah klik tombol")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Mulai Recognition", type="primary", use_container_width=True):
            with st.spinner("⏳ Membuka webcam..."):
                try:
                    st.info("🎥 Webcam terbuka. Posisikan wajah Anda.")
                    
                    emp_id = system.recognize_face()

                    if emp_id:
                        # Ambil data pegawai dari repository (nama)
                        try:
                            peg = system.pegawai_repo.get_by_id(emp_id)
                            nama_user = peg.get('nama') if peg else None
                        except Exception:
                            nama_user = None

                        st.success("✅ AKSES DIBERIKAN!")
                        st.success(f"🚪 Pintu terbuka, Selamat Datang {nama_user}")
                    else:
                        st.error("❌ AKSES DITOLAK!")
                        st.warning("Wajah tidak dikenali")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("Detail Error"):
                        st.code(traceback.format_exc())