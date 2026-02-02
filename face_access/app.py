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
                    st.image(file, use_container_width=True)
                    # Display filename (truncated)
                    filename = file.name if len(file.name) <= 20 else file.name[:17] + "..."
                    st.caption(filename)
            st.divider()            
        with st.form("enrollment_form_video", border=True):         
            submitted = st.form_submit_button(
                "🚀 Mulai Pendaftaran",
                type="primary",
                use_container_width=True
            )
    
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
                use_container_width=True
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
    
    if st.button("🚀 Mulai Recognition", type="primary", use_container_width=True, key="recognition_btn"):
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
                
                # Show success container
                with st.container(border=True):
                    st.markdown(f"""
                    **Status:** ✅ Berhasil
                    
                    **Nama:** {nama_user}
                    
                    **ID:** {emp_id}
                    """)
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