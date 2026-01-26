Face Recognition Door Access System
Sistem akses pintu berbasis face recognition dengan teknologi InsightFace (RetinaFace + ArcFace).

**Struktur Project**
face_access/
│
├── main.py                 
│
├── config/
│   └── settings.py        
│
├── core/
│   ├── camera.py          
│   ├── detector.py         
│   ├── quality.py          
│   ├── liveness.py        
│   ├── embedding.py       
│   └── matcher.py         
│
├── enrollment/
│   └── enroll.py         
│
├── recognition/
│   └── recognize.py        
│
├── db/
│   ├── database.py         
│   ├── pegawai_repo.py
│   ├── embedding_repo.py
│   └── log_repo.py
│
├── utils/
│   ├── timer.py           
│   ├── logger.py          
│   └── math_utils.py
│
├── requirements.txt       
└── README.md
