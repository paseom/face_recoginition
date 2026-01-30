import streamlit as st
from face_access.main import FaceAccessSystem

st.set_page_config(
    page_title="Face Access System",
    layout="centered"
)

# ===== INIT SYSTEM SEKALI =====
if "system" not in st.session_state:
    st.session_state.system = FaceAccessSystem()

system = st.session_state.system

st.title("🔐 Face Access System")

menu = st.radio(
    "Pilih Menu",
    ["🏠 Home", "📝 Pendaftaran Pegawai", "🚪 Face Recognition"]
)

if menu == "🏠 Home":
    st.info("Silakan pilih menu di atas")

elif menu == "📝 Pendaftaran Pegawai":
    st.session_state.page = "enrollment"

elif menu == "🚪 Face Recognition":
    st.session_state.page = "recognition"

if st.session_state.get("page") == "enrollment":
    st.header("📝 Pendaftaran Pegawai")

    nama = st.text_input("Nama Lengkap")
    nip = st.text_input("NIP (10 digit)", max_chars=10)

    metode = st.radio(
        "Metode Pendaftaran",
        ["Upload Gambar", "Rekam Video (Webcam)"]
    )

    if metode == "Upload Gambar":
        uploaded_files = st.file_uploader(
            "Upload 5–10 foto wajah",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

    if st.button("Mulai Pendaftaran"):
        if not nama or not nip:
            st.error("Nama & NIP wajib diisi")
            st.stop()

        if metode == "Upload Gambar":
            if not uploaded_files or len(uploaded_files) < 5:
                st.error("Minimal 5 gambar")
                st.stop()

            # 🔹 Simpan file sementara
            import tempfile, os
            temp_dir = tempfile.mkdtemp()

            for file in uploaded_files:
                with open(os.path.join(temp_dir, file.name), "wb") as f:
                    f.write(file.read())

            success = system.enroll_employee(
                nama=nama,
                nip=nip,
                mode="upload"
            )

        else:
            st.warning("Webcam akan aktif")
            success = system.enroll_employee(
                nama=nama,
                nip=nip,
                mode="video"
            )

        if success:
            st.success("Pendaftaran berhasil!")
        else:
            st.error("Pendaftaran gagal")

if st.session_state.get("page") == "recognition":
    st.header("🚪 Face Recognition")

    st.warning("Webcam akan aktif")

        if st.button("🚀 Mulai Recognition", type="primary", use_container_width=True):
            with st.spinner("⏳ Membuka webcam..."):
                try:
                    st.info("🎥 Webcam terbuka. Posisikan wajah Anda.")

                    emp_id = system.recognize_face()

                    if emp_id:
                        # Ambil nama pegawai dari repository
                        try:
                            peg = system.pegawai_repo.get_by_id(emp_id)
                            nama_user = peg.get('nama') if peg else system.get_current_user_name()
                        except Exception:
                            nama_user = system.get_current_user_name()

                        st.success("✅ AKSES DIBERIKAN!")
                        st.success("🚪 Pintu terbuka, Selamat Datang " + (nama_user or "Pengguna"))
                    else:
                        st.error("❌ AKSES DITOLAK!")
                        st.warning("Wajah tidak dikenali")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("Detail Error"):
                        st.code(traceback.format_exc())
